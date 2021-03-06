#!/usr/bin/env python
#coding=utf-8
import json,sys, time
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest, ReleaseEipAddressRequest, AssociateEipAddressRequest, DescribeEipAddressesRequest, UnassociateEipAddressRequest, AllocateEipAddressRequest
#from common.api.config import GetConfig
#configget = GetConfig()
aliyun = configget.get_config('/home/saltoneops-1.0.0/common/conf/aliyun.conf','aliyun',section='')
access_id = aliyun['access_id']
access_key_secret = aliyun['access_key_secret']
regionid = aliyun['regionid']


#定义一个类供Django调用
class aliapi():
    '''
    这是一个传入EIP后，用来更新弹性IP的一个小程序
    '''
    def __init__(self):
        self.clt = client.AcsClient(
            access_id,
            access_key_secret,
            regionid)
    #通过传入的EIP获取实例的ID以及EIP的ID
    def get_eip_address(self, eip_address):
        request = DescribeEipAddressesRequest.DescribeEipAddressesRequest()
        request.set_accept_format('json')
        request.add_query_param('Status','InUse')
        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print "Get EIP Filad."
            sys.exit()
        BS = {}
        for i in r_dict['EipAddresses']['EipAddress']:
            if i['IpAddress'] == eip_address:
                BS['BS_InstanceId'] = i['InstanceId']
                BS['BS_AllocationId'] = i['AllocationId']
            else:
                pass
        return BS

    #解绑EIP
    def unassociate_eip_address(self, allocationid, instanceid, instancetype='EcsInstance'):
        request = UnassociateEipAddressRequest.UnassociateEipAddressRequest()
        request.set_accept_format('json')
        request.set_AllocationId(allocationid)
        request.add_query_param('InstanceType', instancetype)
        request.set_InstanceId(instanceid)
        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print("Unassociate EIP Address Failed.")
            sys.exit()

        if r_dict.has_key('Code'):
            print(r_dict['Message'])
            sys.exit()
        else:
            return True
    #申请新的EIP
    def create_eip_address(self,regionid='cn-beijing', chargetype='PayByTraffic', bandwidth=50):
        request = AllocateEipAddressRequest.AllocateEipAddressRequest()
        request.set_accept_format('json')
        request.set_Bandwidth(bandwidth)
        request.add_query_param('RegionId', regionid)
        request.add_query_param('InternetChargeType', chargetype)

        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print("Create EIP Address Failed.")
            sys.exit()

        if r_dict.has_key('EipAddress'):
            BS = {}
            BS['ip'] = r_dict['EipAddress']
            BS['id'] = r_dict['AllocationId']
            return BS
        else:
            print(r_dict['Message'])
            sys.exit()
    #绑定新的EIP到实例上
    def associate_eip_address(self,allocationid, instanceid, instancetype='EcsInstance'):
        request = AssociateEipAddressRequest.AssociateEipAddressRequest()
        request.set_accept_format('json')
        request.set_AllocationId(allocationid)
        request.set_InstanceId(instanceid)
        request.add_query_param('InstanceType', instancetype)
        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print("Associate EIP Address Failed.")
            sys.exit()
        if r_dict.has_key('Code'):
            print(r_dict['Message'])
            sys.exit()
        else:
            return r_dict
    #释放旧的EIP
    def delete_eip_address(self,eipid):
        request = ReleaseEipAddressRequest.ReleaseEipAddressRequest()
        request.set_accept_format('json')
        request.set_AllocationId(eipid)
        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print("Delete EIP Address Failed.")
            sys.exit()

        if r_dict.has_key('Code'):
            print(r_dict['Message'])
            sys.exit()
        else:
            return True
    #通过实例ID获取实例的内网IP
    def get_inner_ipaddress(self,allocationid):
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_accept_format('json')
        request.set_PageSize(100)
        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print "Get Inner IP Address Faild."
            sys.exit()
        for i in r_dict['Instances']['Instance']:
            if i['InstanceId'] == allocationid:
                inner_ipaddress = i['VpcAttributes']['PrivateIpAddress']
                inner_ipadd = inner_ipaddress['IpAddress'][0]
        return inner_ipadd
    #根据实例ID获取EIP
    def get_enter_ipaddress(self,allocationid):
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_accept_format('json')
        request.set_PageSize(100)
        try:
            result = self.clt.do_action_with_exception(request)
            r_dict = json.loads(result)
        except:
            print "Get Inner IP Address Faild."
            sys.exit()
        for i in r_dict['Instances']['Instance']:
            if i['InstanceId'] == allocationid:
                enter_ipaddress = i['VpcAttributes']['PrivateIpAddress']
                enter_ipadd = enter_ipaddress['IpAddress'][0]
        return enter_ipadd

    #返回新的EIP以及实例内网IP
    def change_eip(self, eip, regionid='cn-beijing',chargetype='PayByTraffic', bandwidth=100,instancetype='EcsInstance'):
        re_eip = self.get_eip_address(eip)
        if re_eip.has_key('BS_AllocationId'):
            allocationid = re_eip['BS_AllocationId']
            instanceid = re_eip['BS_InstanceId']
            unassociate_eip = self.unassociate_eip_address(allocationid, instanceid, instancetype)
            iplist = {}
            if unassociate_eip:
                create_eip = self.create_eip_address(regionid, chargetype, bandwidth)
                allocationid = create_eip['id']
                if create_eip:
                    while True:
                        enter_ipadd = self.get_enter_ipaddress(instanceid)
                        if not enter_ipadd:
                            self.associate_eip_address(allocationid, instanceid, instancetype)
                            eipid = re_eip['BS_AllocationId']
                            delete_eip = self.delete_eip_address(eipid)
                            if delete_eip:
                                iplist['new_eip'] = create_eip['ip']
                                iplist['new_innerip'] = self.get_inner_ipaddress(instanceid)
                        else:
                            continue
                        time.sleep(3)
        else:
            return "Please Enter Right Eip"
            sys.exit()
        return iplist


if __name__=="__main__":
    a = aliapi()
    print a.change_eip('',bandwidth=200)

