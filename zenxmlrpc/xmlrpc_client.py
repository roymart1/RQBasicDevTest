import xmlrpc.client


class XMLRPCClient:

    def __init__(self):
        # self.server = "10.20.22.68"
        self.server = "127.0.0.1"
        self.port = 60000

    def call_server(self):
        proxy = xmlrpc.client.ServerProxy(f"http://{self.server}:{str(self.port)}/")

        result = proxy.getClientIp()

        proxy.call_handler2("disp" ,"function", ['PAram1', 2, 'param3'], "param4")
        print(result)

    def call_server(self):
        proxy = xmlrpc.client.ServerProxy(f"http://{self.server}:{str(self.port)}/")

        result = proxy.getClientIp()

        proxy.call_handler2("disp" ,"function", ['PAram1', 2, 'param3'], "param4")
        print(result)


if __name__ == '__main__':
    client = XMLRPCClient()
    client.call_server()

