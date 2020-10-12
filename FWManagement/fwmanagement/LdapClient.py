from ldap3 import (
    ALL,
    LEVEL,
    SUBTREE,
    AttrDef,
    Attribute,
    Connection,
    Entry,
    ObjectDef,
    OperationalAttribute,
    Reader,
    Server,
    Writer,
)


class LdapClient(object):
    def __init__(self, ldap_server, ldap_basedn, ldap_user, ldap_password):
        self.__ldap_server = Server(ldap_server, get_info=ALL)
        self.__ldap_user = ldap_user
        self.__ldap_password = ldap_password
        self.ldap_basedn = ldap_basedn

    def get_personDetails(self, person):
        with Connection(
            self.__ldap_server,
            self.__ldap_user,
            self.__ldap_password,
            auto_bind=True,
        ) as conn:
            r = Reader(
                conn, ObjectDef(["inetOrgPerson"], conn), person,
            )
            r.search()
        return r.entries[0]

    def find_byEmail(self, email, search_base):
        found = []
        with Connection(
            self.__ldap_server,
            self.__ldap_user,
            self.__ldap_password,
            auto_bind=True,
        ) as conn:
            r = Reader(
                conn, ObjectDef(["inetOrgPerson"], conn), search_base,
                "mail:=" + email,
            )
            r.search()
            for entry in r.entries:
                found.append(entry.entry_dn)
        return found

    def get_lists(self, search_base):
        ldap_lists = []
        with Connection(
            self.__ldap_server,
            self.__ldap_user,
            self.__ldap_password,
            auto_bind=True,
        ) as conn:
            r = Reader(conn, ObjectDef(["groupOfURLs"], conn), search_base)
            r.search()
            for entry in r.entries:
                ldap_lists.append(entry.entry_dn)
        return ldap_lists

    def get_groups(self, search_base):
        ldap_groups = []
        with Connection(
            self.__ldap_server,
            self.__ldap_user,
            self.__ldap_password,
            auto_bind=True,
        ) as conn:
            r = Reader(
                conn, ObjectDef(["groupOfUniqueNames"], conn), search_base
            )
            r.search()
            for entry in r.entries:
                ldap_groups.append(entry.entry_dn)
        return ldap_groups

    def get_listMembers(self, listname, search_base):
        memberlist = []
        with Connection(
            self.__ldap_server,
            self.__ldap_user,
            self.__ldap_password,
            auto_bind=True,
        ) as conn:
            bswlist = ObjectDef(["groupOfURLs"], conn)
            bswlist += "uniqueMember"
            bswmember = ObjectDef(["inetOrgPerson"], conn)
            r = Reader(conn, bswlist, search_base, "cn:=" + listname)
            r.search()
            for entry in r:
                # print(entry.entry_attributes_as_dict)
                # print(entry['uniqueMember'])
                for item in entry["uniqueMember"]:
                    # print(item.split(',')[0].split('=')[1])
                    r2 = Reader(
                        conn,
                        bswmember,
                        self.ldap_basedn,
                        "cn:=" + item.split(",")[0].split("=")[1],
                    )
                    r2.search()
                    for member in r2:
                        memberlist.append(
                            (
                                member["sn"][0] + "," + member["givenName"][0],
                                member["mail"][0],
                            )
                        )
        return memberlist

    def get_groupMembers(self, groupname, search_base):
        memberlist = []
        with Connection(
            self.__ldap_server,
            self.__ldap_user,
            self.__ldap_password,
            auto_bind=True,
        ) as conn:
            bswmember = ObjectDef(["inetOrgPerson"], conn)
            bswgroup = ObjectDef(["groupOfUniqueNames"], conn)
            r = Reader(conn, bswgroup, search_base, "cn:=" + groupname)
            r.search()
            for entry in r:
                # print(entry.entry_attributes_as_dict)
                # print(entry['uniqueMember'])
                for item in entry["uniqueMember"]:
                    r2 = Reader(
                        conn,
                        bswmember,
                        self.ldap_basedn,
                        "cn:=" + item.split(",")[0].split("=")[1],
                    )
                    r2.search()
                    if len(r2) == 0:
                        add_members = self.get_groupMembers(
                            item.split(",")[0].split("=")[1], search_base
                        )
                        memberlist.extend(add_members)
                    else:
                        for member in r2:
                            memberlist.append(
                                (
                                    member["sn"][0]
                                    + ","
                                    + member["givenName"][0],
                                    member["mail"][0],
                                )
                            )
        return memberlist
