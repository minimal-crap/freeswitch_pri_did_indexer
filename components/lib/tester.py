import requests
import ESL
import paramiko

from components.conf import settings
from components.lib import logger, common_utils

class PRITester:
    pri_info_document = {
        "ipaddr_private": "",
        "ipaddr_public": "",
        "hostname": "",
        "epoch_added": "",
        "epoch_updated": "",
        "card_info": {},
        "wanpipe": {}
    }

    wanpipe_info_document = {
        "hangup_cause": "",
        "physical": "",
        "signalling": "",
        "outgoing": "",
        "outgoing_caller_id": ""
    }

    def __init__(self,
                 server=None,
                 lower_port=8056,
                 upper_port=8057,
                 testing=False
                 ):
        self.server_details = dict()
        self.freeswitch_simulator_url = "http://localhost:1611/originate_call/1111"
        self.testing = testing
        self.redis_wanpipe_key = "wan_pipes"
        self.server_details["server_private_address"] = server
        self.server = server
        self.server_public_address = ""
        self.server_host_name = ""
        self.lower_port = lower_port
        self.upper_port = upper_port
        self.destination_number = "XXXXXXXXXX"
	
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.server, **settings.SERVERS[self.server])

        if self.server is None:
            raise Exception("Server not defined while initiating object")

        # necessary commands
        self.check_running_kombu_dialer_command = \
            "ps aux|grep kombu"

        try:
            # preparing logger for redirecting output
            self.error_logger = logger.Logger("pri_tester_error_log",
                                              file_handler=True,
                                              stream_handler=True)
            self.debug_logger = logger.Logger("pri_tester_debug_log",
                                              file_handler=True,
                                              stream_handler=True)
            self.error_logger = self.error_logger.logger
            self.debug_logger = self.debug_logger.logger

            # preparing freeswitch connection objects
            self.lower_pris_con = ESL.ESLconnection(self.server,
                                                    lower_port,
                                                    "ClueCon")

            self.upper_pris_con = ESL.ESLconnection(self.server,
                                                    upper_port,
                                                    "ClueCon")

        except Exception as err:
            self.error_logger.error(err.message + "PRITester::init")

    def get_functional_pris(self, port):
        """
        returns functional pris at the specified server
        using the show spans command of freeswitch
        :param port:
        :return:
        """
        try:
            if port is not None:
                functional_pri_list = []
                sangoma_span_command = "ftdm sangoma_isdn show_spans"
                if int(port) == self.lower_port:
                    response = self.lower_pris_con.api(sangoma_span_command)

                elif int(port) == self.upper_port:
                    response = self.upper_pris_con.api(sangoma_span_command)

                else:
                    raise Exception("Invalid port number %d while attempting to\
                    get functional pri list PRITester::get_functional_pris" % port)

                # processing the show spans command response need more refinement
                for output_line in response.getBody().split("\n"):
                    status_fields = output_line.split()
                    if output_line.find("Command executed OK") == -1 and len(status_fields) > 0:
                        pri_status = status_fields[1].split(":")[1]
                        if pri_status.lower() == "ok":
                            functional_pri_list.append(int(status_fields[0].split(":")[1][2:]))
                return functional_pri_list

            else:
                raise Exception("Port not specified while fetching functional pri\
                list PRITester::get_functional_pris")
        except Exception as err:
            self.error_logger.error(err.message + " PRITester::get_functional_pris")

    def get_running_pris(self):
        """
        creates a remote connection with server and executes
        grep on ps command to fetch all running PRIs
        :param port: Integer format port number
        :return: List type running pris
        """
        try:
            running_pris_list = []
            output = self.ssh.exec_command(self.check_running_kombu_dialer_command)
            for line in output[1].readlines():
                line = line.split()
                if self.server in line and "-g" in line:
                    running_pris_list.append(
                        int(
                            line[line.index("-g")+1][2:]
                        )
                    )
            return running_pris_list
        except Exception as err:
            self.error_logger.error(err.message + " PRITester::get_running_pris")
            return None

    def dial_individual_pri(self,
                            pri_channel_id,
                            port):
        """
        takes pri channel id and port as parameter and
        dials through the remote freeswitch server and returns
        the output status of the dialled call in string format
        :param pri_channel_id: Integer type pri channel id
        :param port: Integer type port
        :return: String type status message
        """

        if int(port) not in [self.lower_port, self.upper_port]:
            raise Exception("Invalid port number %d while dialing list of\
            Individual PRI %d pri::CheckPRIs::getRunningPRI"
                            % int(port, pri_channel_id)
                            )

        try:
            kombu_dialer_command = \
                "{ignore_early_media=true}freetdm/wp%d/a/%s &playback(/var/lib/viva/sounds/untitled_pp.wav)" % \
                (int(pri_channel_id),
                 self.destination_number
                 )

            self.debug_logger.debug("Testing PRI : %s" %
                                    ("wp"+str(pri_channel_id))
                                    )

            self.debug_logger.debug(kombu_dialer_command)
            if self.testing:
                response = requests.get(self.freeswitch_simulator_url)
                if response.status_code == 200:
                    response_dict = ["fs_sim", "SUCCESS"]
                else:
                    response_dict = ["fs_sim", str(response.status_code)]
                return response_dict

            if int(port) == self.lower_port:

                response = \
                    self.lower_pris_con.api("originate",
                                            kombu_dialer_command)

                return response.getBody().strip().split(" ")

            else:
                response = \
                    self.upper_pris_con.api("originate",
                                            kombu_dialer_command)
                return response.getBody().strip().split(" ")

        except Exception as err:
            self.error_logger.error(
                err.message + " PRITester::dial_individual_pri"
            )
            return "error"

    def get_server_details(self):
        try:

            response = self.ssh.exec_command("echo $HOSTNAME")
            self.server_host_name = str(response[1].readlines()[0])
            self.server_details["server_host_name"] = self.server_host_name
            response = self.ssh.exec_command("curl wgetip.com")
            self.server_public_address = str(response[1].readlines()[0])
            self.server_details["server_public_address"] = self.server_public_address

        except Exception as err:
            self.error_logger.error(
                err.message + " PRITester::get_server_details"
            )

    def run_checking(self):
        try:
            self.debug_logger.debug(
                "Initiating PRI checking at %s" % self.server
            )

            self.debug_logger.debug(
                "Checking functional PRIs at port {}".format(
                    self.lower_port
                )
            )
            functional_pris = self.get_functional_pris(self.lower_port)
            functional_pris.sort()
            print(functional_pris)

            self.debug_logger.debug(
                "Checking running PRIs at server {}".format(
                    self.server
                )
            )
            running_pris = self.get_running_pris()
            running_pris.sort()
            print running_pris

            non_running_pris = list(set(functional_pris) - set(running_pris))
            self.debug_logger.debug(
                "%d Non running PRIs found at port %d" %
                (
                    len(non_running_pris),
                    self.lower_port
                )
            )
            print non_running_pris
            self.debug_logger.debug(
                "Dialling %d non running RPIs for port %d" %
                (
                    len(non_running_pris),
                    self.lower_port
                )
            )
            for pri in non_running_pris:
                status = self.dial_individual_pri(pri,
                                                  self.lower_port)
                self.debug_logger.debug(status)

            self.debug_logger.debug(
                "Checking functional PRIs at port {}".format(
                    self.upper_port
                )
            )
            functional_pris = self.get_functional_pris(self.upper_port)
            functional_pris.sort()
            print(functional_pris)

            non_running_pris = list(set(functional_pris) - set(running_pris))
            self.debug_logger.debug(
                "%d Non running PRIs found at port %d" %
                (
                    len(non_running_pris),
                    self.upper_port
                )
            )
            print non_running_pris
            self.debug_logger.debug(
                "Dialling %d non running RPIs for port %d" %
                (
                    len(non_running_pris),
                    self.upper_port
                )
            )
            for pri in non_running_pris:
                status = self.dial_individual_pri(pri,
                                                  self.upper_port)
                self.debug_logger.debug(status)
        except Exception as err:
            self.error_logger.error(err.message + " PRITester::run_checking")


# def main():
#     server = None
#     parser_obj = argparse.ArgumentParser(description="parse me may be!!")
#     parser_obj.add_argument('--server',
#                             '-s',
#                             dest='server',
#                             action='store',
#                             type=str,
#                             default=None
#                             )
#     parsed_args = parser_obj.parse_args()
#     server = parsed_args.server
#
#     pri_tester_obj = PRITester(server=server)
#     pri_tester_obj.run_checking()
#
#
# if __name__ == '__main__':
#     main()
