import argparse
import dns.query
import dns.message

IP = 0
TARGET = ''


# a function to do the iterative search procedure
def search(query_name, source_ip, source_port, LDNS_ip, target_server_name, display, rdtype):
    while True:
        send = dns.message.make_query(query_name, rdtype)  # build a query to the query_name, the type is rdtype
        send.flags = 0x0020
        response = dns.query.udp(send, LDNS_ip, source=source_ip,
                                 source_port=source_port)  # send the query to LDNS_ip and receive a udp response

        # display the process in the log file when detecting key word "display"
        if display is True:
            print("(", source_ip, "#", source_port, ") send query(", query_name, rdtype, "IN rd=0) to DNS Server:(",
                  target_server_name, LDNS_ip, "#53)")
            print(response)
            print()

        answer = response.answer
        additional = response.additional
        authority = response.authority

        # Check if the answer is valid
        if answer != []:
            for i in answer:
                if i.rdtype == 1:  # type is A, answer is valid
                    return i, query_name  # return the final answer and the query name

        # a response with ONLY Authority RRs and Additional RRs
        if answer == [] and additional != [] and authority != []:
            # pick the IP address of the DNS server in the first record in the Additional RRs
            # use this address as the destination IP of the next query
            LDNS_ip = pick(additional[0])
            target_server_name = pick(authority[0])

        # a response with Authority RRs, Additional RRs and type miss matched Answer RRs
        elif answer != [] and additional != [] and authority != []:

            # continue to do the iterative queries to the name server
            # update the following three variables
            LDNS_ip = pick(additional[0])
            target_server_name = pick(authority[0])
            query_name = pick(answer[0])

        # a response with Only Authority RRs
        elif answer == [] and additional == [] and authority != []:
            if rdtype == 'NS':
                # Continue the query but change the query_name to the authority server name
                return search(pick(authority[0]), source_ip, source_port, LDNS_ip, target_server_name, display, 'A')
            else:
                # invoke a new query
                LDNS = search("<Root>", source_ip, source_port, LDNS_ip, target_server_name, display, 'NS')
                LDNS_ip = pick(LDNS[0])
                target_server_name = LDNS[1]
                # continue the query but change the query_name to the authority server name
                result = search(pick(authority[0]), source_ip, source_port, LDNS_ip, target_server_name, display, 'A')
                LDNS_ip = pick(result[0])
                target_server_name = result[1]

        # a response with ONLY type miss matched Answer RRs
        elif answer != [] and additional == [] and authority == []:
            temp_query_name = pick(answer[0])
            # Restart the iterative query
            # Keep the local dns ip and target name original by using the global variables "IP" and "TARGET"
            LDNS = search("<Root>", source_ip, source_port, IP, TARGET, display, 'NS')
            LDNS_ip = pick(LDNS[0])
            target_server_name = LDNS[1]
            # use the query name from the response to replace the original
            return search(temp_query_name, source_ip, source_port, LDNS_ip, target_server_name, display, 'A')


# a function to pick out the ip or server name in RRsets
def pick(RRs):
    lst = RRs.to_text().split('\n')[0].split(' ')
    index = int()
    for i in lst:
        if i == 'IN':  # The key information always lie after the next element of 'IN'
            index = lst.index(i) + 2
            break
    return lst[index]


if __name__ == '__main__':

    # Parse the input
    parse = argparse.ArgumentParser()
    parse.add_argument('-q')
    parse.add_argument('-s')
    parse.add_argument('-p')
    parse.add_argument('-server')
    parse.add_argument('-display', action='store_true')
    a = parse.parse_args()
    dic = vars(a)

    # Pick out the key elements of the instruction
    query_name = dic['q']
    source_ip = dic['s']
    source_port = int(dic['p'])
    LDNS_ip = dic['server']
    display = a.display

    # testing codes:
    # python dns_iterative_q_client.py -q www.baidu.com -s 10.17.32.243 -p 14000 -server 8.8.8.8
    # python dns_iterative_q_client.py -q www.example.com -s 10.17.32.243 -p 14000 -server 8.8.8.8
    # python dns_iterative_q_client.py -q www.sina.com -s 10.17.32.243 -p 14000 -server 8.8.8.8
    # python dns_iterative_q_client.py -q www.baidu.com -s 10.17.32.243 -p 14000 -server 8.8.8.8 -display>q_www.baidu.com_14000_8.8.8.8_display.log
    # python dns_iterative_q_client.py -q www.example.com -s 10.17.32.243 -p 14000 -server 8.8.8.8 -display >q_www.example.com_14000_8.8.8.8_display.log
    # python dns_iterative_q_client.py -q www.sina.com -s 10.17.32.243 -p 14000 -server 8.8.8.8 -display >q_www.sina.com_14000_8.8.8.8_display.log

    # get the local dns server's ip and name
    LDNS = search("<Root>", source_ip, source_port, LDNS_ip, "Local DNS Server", display, 'NS')
    LDNS_ip = pick(LDNS[0])
    target_server_name = LDNS[1]

    # global variable, for storing the very original local DNS ip and target server name
    # Used when encountering a response with ONLY type miss matched Answer RRs
    IP = LDNS_ip
    TARGET = target_server_name

    # get the query servers' ip and name
    answer = search(query_name, source_ip, source_port, LDNS_ip, target_server_name, display, 'A')

    # Output
    print("Final Answer:")
    print("Name:", answer[1])
    print("Addresses:")
    for i in answer[0]:
        print(pick(i))
    if query_name != answer[1]:
        print("Aliases:", query_name)
