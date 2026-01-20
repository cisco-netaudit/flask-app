"""
Network device auditing module.

This module provides the AuditService class, which performs audits on a list
of network devices using specified checks.
"""

import os
import inspect
import re
import socket
import textwrap
import importlib.util
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
from netcore import GenericHandler

class AuditService:
    """
    Service class to perform network device audits using configurable checks.
    """

    def __init__(self, devices, check_dir, facts_dir=None, context=None):
        """
        Initialize the AuditService.

        Args:
            devices (list): List of devices to audit.
            check_dir (str): Directory containing check modules.
            facts_dir (str): Directory containing fact-gathering modules.
            context (dict, optional): Additional context for audit. Defaults to None.
        """
        self.devices = devices
        self.checks_dir = check_dir
        self.context = context
        self.facts_dir = facts_dir
        self.results = {}
        self.futures = []
        self.gatherers = {}
        if self.facts_dir:
            self.load_facts()

    def get_check_instance(self, check_file, device):
        """
        Dynamically load and return an instance of a check class from a file.

        Args:
            check_file (str): Filename of the check module.
            device (str): Hostname/IP of the device to run the check against.

        Returns:
            object: Instance of the check class (CHECK_CLASS) in the module.
        """
        file_path = os.path.join(self.checks_dir, check_file)
        module_name = file_path.replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        logging.debug(f"Loaded check module '{check_file}' for device '{device}'")
        return getattr(module, "CHECK_CLASS")(device, self.context)

    def obt_conn(self, device, session):
        """
        Establish a network connection to a device using GenericHandler.

        Args:
            device (str): Device hostname or IP.
            session (dict): Session credentials.

        Returns:
            GenericHandler | None: Connection object if successful, else None.
        """
        proxy = {
            'hostname': session['jumphost_ip'],
            'username': session['jumphost_username'],
            'password': session['jumphost_password']
        } if session['jumphost_ip'] else None

        try:
            conn = GenericHandler(
                hostname=device,
                username=session['network_username'],
                password=session['network_password'],
                proxy=proxy,
                handler='NETMIKO'
            )
            logging.info(f"Connected to device '{device}' successfully")
            return conn
        except Exception as e:
            logging.error(f"Connection failed for '{device}': {e}")
            return

    def start_thread_executor(self, max_workers=8):
        """
        Start the thread pool executor to perform audits concurrently.

        Args:
            max_workers (int, optional): Maximum number of threads. Defaults to 8.

        Returns:
            list: Futures of submitted tasks.
        """
        logging.info("Starting audit thread pool execution...")
        executor = ThreadPoolExecutor(max_workers=max_workers)
        for device_data in self.devices:
            future = executor.submit(self.audit_task, device_data)
            self.futures.append(future)
        return self.futures

    def wait_for_completion(self):
        """
        Wait for all audit tasks to complete.
        """
        for future in as_completed(self.futures):
            future.result()
        logging.info("All device audits completed.")

    def _get_device_fqdn(self, device, conn):
        """
        Resolve and return the fully qualified domain name (FQDN) of the device.
        """
        if re.search(r"^\d{1,3}(\.\d{1,3}){3}$", device):
            try:
                device_fqdn = socket.gethostbyaddr(device)[0]
                return device_fqdn
            except socket.herror:
                if conn:
                    domain_name_output = conn.sendCommand("show running-config | include domain")
                    match = re.search(r'^ip domain[- ]name\s+(\S+)', domain_name_output, re.M)
                    if match:
                        return f"{conn.base_prompt}.{match.group(1)}"
                    return conn.base_prompt
                return device
        else:
            return device

    def audit_task(self, device_data):
        """
        Perform all checks on a given device.

        Args:
            device_data (dict): Dictionary containing device info and checks.
        """
        device = device_data.get("device")
        session = device_data.get("session")
        check_list = device_data.get("check_list")

        self.results[device] = {
            "last_audit": datetime.datetime.now().isoformat(),
            "login": None,
            "hostname": device,
            "raw": {},
            "facts": {},
            "checks": {check_file: {"status": 0, "observation": "", "comments": []} for check_file in check_list},
        }

        conn = self.obt_conn(device, session)

        self.results[device]["login"] = bool(conn)
        self.results[device]["hostname"] = self._get_device_fqdn(device, conn)

        if not conn:
            logging.error(f"Skipping device '{device}' due to connection failure")
            self.results[device]["status"] = 2
            return

        if self.gatherers:
            self.results[device]["facts"] = self.gather_facts(conn)

        for check_file in check_list:
            try:
                check_inst = self.get_check_instance(check_file, device)
                last_request = None

                while check_inst.REQUESTS:
                    current_request = (
                        check_inst.REQUESTS.get("device"),
                        check_inst.REQUESTS.get("command"),
                        check_inst.REQUESTS.get("handler"),
                    )

                    if current_request == last_request:
                        break

                    req_device, req_cmd, handler_name = current_request

                    if req_device != device:
                        if self.results.get(device).get("raw").get(f"{req_device}:{req_cmd}"):
                            output = self.results[device]["raw"][f"{req_device}:{req_cmd}"]
                        else:
                            conn.disconnect()
                            conn = self.obt_conn(req_device, session)
                            output = conn.sendCommand(req_cmd)
                        self.results[device]["raw"][f"{req_device}:{req_cmd}"] = output
                    else:
                        if self.results.get(device)["raw"].get(req_cmd):
                            output = self.results[device]["raw"][req_cmd]
                        else:
                            output = conn.sendCommand(req_cmd)
                        self.results[device]["raw"][req_cmd] = output

                    getattr(check_inst, handler_name)(req_device, req_cmd, output)
                    last_request = current_request

                self.results[device]["checks"][check_file] = check_inst.RESULTS
                logging.debug(f"Check '{check_file}' completed for '{device}'")
            except Exception as e:
                logging.error(f"Error executing check '{check_file}' on '{device}': {e}")

        self.results[device]["status"] = 1
        for check_file, check_result in self.results[device]["checks"].items():
            if check_result.get("status") in [2, 5]:
                self.results[device]["status"] = 2
                break

        conn.disconnect()
        logging.info(f"Audit task completed for device '{device}'")


    def load_facts(self):
        """
        Load fact-gathering functions from the specified facts directory.
        """
        for facts_module in os.listdir(self.facts_dir):
            if facts_module.endswith(".py") and not facts_module.startswith("__"):
                path = os.path.join(self.facts_dir, facts_module)
                module_name = facts_module.replace(".py", "")
                spec = importlib.util.spec_from_file_location(module_name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for _, func in inspect.getmembers(module, inspect.isfunction):
                    match = re.match(r"^gather_([a-zA-Z0-9_]+)$", func.__name__)
                    if not match:
                        continue

                    name = match.group(1)
                    gatherer_id = f"{module_name}.{name}"
                    self.gatherers[gatherer_id] = {
                        "name": name,
                        "func": func,
                        "path": path,
                        "description": inspect.getdoc(func) or "No description.",
                        "code": textwrap.dedent(inspect.getsource(func)),
                    }

    def gather_facts(self, conn):
        """
        Gather facts from the device using loaded gatherer functions.
        """
        facts = {}
        for name, meta in self.gatherers.items():
            func = meta["func"]
            try:
                result = func(conn)
                if isinstance(result, dict):
                    facts.update(result)
            except Exception as exc:
                logging.error(f"Error running gatherer '{name}': {exc}")
        return facts