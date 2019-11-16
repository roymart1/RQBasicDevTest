import xmlrpc.client


class XMLRPCClient:

    # self.server = "10.20.22.68"
    def __init__(self):
        self.server = "127.0.0.1"
        self.port = 60000
        self.proxy = xmlrpc.client.ServerProxy(f"http://{self.server}:{str(self.port)}/")


    def call_dynamic_plugins(self):
        originatingIP = self.proxy.getClientIp()

        result = self.proxy.CallHandler("PARA_GRIPPER" ,"setServerOff", 10, "Allo", 55.86)
        print(result)
        result = self.proxy.CallHandler("PARA_GRIPPER" ,"setServerOn", 10, "Allo")
        print(result)
        result = self.proxy.CallHandler("VACUUM_VOLTS", "MeasureMaxVolts")
        print(result)
        result = self.proxy.CallHandler("VACUUM_VOLTS", "LowerAvgLoad", 10, 2.33)
        print(result)



    def get_all_loaded_dispatch(self):
        result = self.proxy.DH_GetLoadedPlugins()
        print(result)
        return result

    def get_methods_for_plugin(self, dispatch_name):
        result = self.proxy.DH_GetPluginMethods(dispatch_name)
        print(result)



if __name__ == '__main__':
    client = XMLRPCClient()
    client.call_dynamic_plugins()
    tags = client.get_all_loaded_dispatch()
    for tag in tags:
        print("DISPATCH ->" + tag)
        print("METHODS ->")
        client.get_methods_for_plugin(tag)
    print("Over and out")