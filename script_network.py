import urllib3
import json
import requests
import csv
from datetime import datetime


now = datetime.now()


date_time_str = now.strftime("%Y-%m-%d %I:%M:%S %p")


urllib3.disable_warnings()




def get_vs_name(pe_ip, username, password,host_uuid):
    links=[]
    body={"entity_type":"virtual_switch",
"group_member_attributes":[{"attribute":"name"},{"attribute":"host_nic"}],
"query_name":"prism:EBQueryModel",
"filter_criteria":f"node=={host_uuid}"}
    url = f"https://{pe_ip}:9440/PrismGateway/services/rest/v1/groups"


    headers = {"Content-Type": "application/json", "charset": "utf-8"}  

    
    try:
        response = requests.post(url, auth=(username, password), headers=headers, verify=False, json=body)
        #print(response.status_code)
        if response.status_code != 200:
        #print("Error in getting VMs for PE:", Pe_IP)
            
            return None
        for o in response.json()["group_results"][0]["entity_results"]:
            vs = o["data"][0]["values"][0]["values"][0]
            if vs == "virbr0":
                continue
            nics = o["data"][1]["values"][0]["values"]
            links.append({"vs":vs,"nics":nics})
    
        return links
    
    except Exception:
        return None
    #print(response.json())
    
    
    



def get_speed(pe_ip, username, password,host_uuid,nic_uuid):

    url = f"https://{pe_ip}:9440/PrismGateway/services/rest/v1/hosts/{host_uuid}/host_nics/{nic_uuid}/stats?metrics=network.received_rate_kBps%2Cnetwork.transmitted_rate_kBps%2Cnetwork.dropped_received_pkts%2Cnetwork.dropped_transmitted_pkts%2Cnetwork.error_received_pkts"
    headers = {"Content-Type": "application/json", "charset": "utf-8"}
    try:
        response = requests.get(url, auth=(username, password), headers=headers, verify=False)
        if response.status_code != 200:
        #print("Error in getting VMs for PE:", Pe_IP)
            return None,None
        rx = response.json()["statsSpecificResponses"][0]["values"][0]
        tx = response.json()["statsSpecificResponses"][1]["values"][0]
        return rx,tx
    except Exception:
        return None,None
    
    


    


def get_all_nics(pe_ip, username, password,host_uuid):
        url = f"https://{pe_ip}:9440/PrismGateway/services/rest/v1/groups"
        headers = {"Content-Type": "application/json", "charset": "utf-8"}


        body={"entity_type":"host_nic","group_member_attributes":
              [{"attribute":"link_capacity"},{"attribute":"name"},
               {"attribute":"port_name"},{"attribute":"link_detected"}],
               "query_name":"prism:EBQueryModel","filter_criteria":f"node=={host_uuid}"}
        
     
        try:
            response = requests.post(url, auth=(username, password), headers=headers, verify=False, json=body)
            if response.status_code != 200:
        #print("Error in getting VMs for PE:", Pe_IP)
                return None
            nics = []
            for o in response.json()["group_results"][0]["entity_results"]:
                if o["data"][3]["values"][0]["values"][0] == "0":
                    continue
                nics.append({"port_name":o["data"][2]["values"][0]["values"][0],"uuid":o["entity_id"],"vs":"NA"})
            # print("Host UUID:",host_uuid)
            # print(active_links)
            # print()
            return nics
        
        except Exception:
            return None
        
        
def get_hosts(pe_ip, username, password):

    headers = {"Content-Type": "application/json", "charset": "utf-8"}

    url = f"https://{pe_ip}:9440/PrismGateway/services/rest/v1/hosts"

    try:
        response = requests.get(url, auth=(username, password), headers=headers, verify=False)
    #print(response.status_code)
        if response.status_code != 200:
        #print("Error in getting VMs for PE:", Pe_IP)
            return None
        
        hosts_data=[]
        print("\t Getting Virtual Switches for PE:", pe_ip)

        for host in response.json()["entities"]:
        
            links = get_vs_name(pe_ip, username, password,host["uuid"])
            if links is None:
                continue
        #print(links)
            nics = get_all_nics(pe_ip, username, password,host["uuid"])
            if nics is None:
                continue
        #print(nics)
        #print()
            for n in nics:
                for l in links:
                    if n["uuid"] in l["nics"]:
                        n["vs"] = l["vs"].replace("br","vs")
                        break
                        
            hosts_data.append({"uuid": host["uuid"], "name": host["name"],"cluster":pe_ip,"nics":nics})

        hosts_data = sorted(hosts_data,key=lambda x:x["name"])
    #print(hosts_data)
        return hosts_data
    
    except Exception:
        return None
    #print(response.json()["entities"])
    




def main():

    data = []
    with open("hosts.json","w") as f:
        json.dump(data, f)

    with open("creds.csv","r") as f:
        reader = csv.reader(f)
        for row in reader:
            username = row[0]
            password = row[1]

    ouptut_json = []
    with open("result.csv","w",newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date Time","Cluster", "Host Name","Interface Name","Virtual Switch","Link Status","Network Received Speed (Rx)(kBps)","Network Transmitted Speed (Tx)(kBps)"])

        with open("pe.csv") as pe_csv:
            reader = csv.reader(pe_csv)
            for row in reader:
                try:
                    print("\t Getting hosts from PE:", row[0])
                    res = get_hosts(row[0], username, password)
                    
                #print(res)
                    if not res:
                        raise Exception
                    #print(res)
                    ouptut_json+=res
                    print("\t Getting Network Speeds for Connected Links from PE:", row[0])
                    for h in res:
                        host_uuid = h["uuid"]
                        for n in h["nics"]:
                            rx,tx  = get_speed(row[0], username, password,host_uuid,n["uuid"])
                            if rx is None and tx is None:
                                writer.writerow([datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),row[0], h["name"],n["port_name"],"Connected","NA","NA"])
                            writer.writerow([datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),row[0], h["name"],n["port_name"],n["vs"],"Connected",rx,tx])

                except Exception:
                    print("\t Error in getting Hosts from PE", row[0])
                print()
    
    with open("hosts.json","w") as f:
        json.dump(ouptut_json, f, indent=4)

if __name__ == '__main__':
    print()
    main()