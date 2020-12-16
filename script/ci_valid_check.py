
'''
This is a bot for openEuler competition repository manage.
'''

import argparse
import yaml
import os
import sys
import requests
import json

TEAMINFO = "TEAM_INFO/teaminfo.yaml"
LEGALIDS = "TEAM_INFO/legalids.yaml"
COMMUNITY = "openeuler2020"
ORG_API = "https://gitee.com/api/v5/orgs/"
USER_API = "https://gitee.com/api/v5/users/"
CLA_API = "https://clasign.osinfra.cn/api/v1/individual-signing/gitee/openeuler"

def team_has_keyfield(team):
    issue_found = 0
    if 'teamid' not in team.keys():
        print("There is no team id.")
        issue_found += 1
        return issue_found
    if 'teamname' not in team.keys() or len(team['teamname']) == 0:
        print("There is no team name.")
        issue_found += 1
        return issue_found
    if 'description' not in team.keys():
        print("There is no team description, we will add it.")
    if 'repository' not in team.keys() or len(team['repository']) == 0:
        print("There is no repository name.")
        issue_found += 1
        return issue_found
    if 'repotype' not in team.keys() or len(team['repotype']) == 0:
        print("There is no repo type.")
        issue_found += 1
        return issue_found
    if 'tutor' not in team.keys() or len(team['tutor']) == 0:
        print("There is no tutor here.")
        issue_found += 1
        return issue_found
    if 'members' not in team.keys() or len(team['members']) == 0:
        print("There is no team member here.")
        issue_found += 1
        return issue_found
    return issue_found


def repo_member_valid_check(user, token):
    '''
    check someone in repository is valid or not.
    :param user:
    :param token:
    :return:
    '''
    print(">>>>>>>>Begin user valid check.")
    issue_found = 0
    '''
    check user gitee id valid
    '''
    user_url = USER_API + user['giteeid']
    param = {'access_token': token}
    response = requests.get(user_url, params=param)
    if response.status_code != 200:
        print("Get User {} information from gitee failed.".format(user['giteeid']))
        issue_found += 1
        return
    '''
    check user cla sign.
    '''
    param = {'email': user['email']}
    response = requests.get(CLA_API, params=param)
    if response.status_code != 200:
        print("Get User:{} cla info failed.".format(user['giteeid']))
        issue_found += 1
        return issue_found

    jstr = json.loads(response.text)
    if 'data' not in jstr.keys():
        issue_found += 1
        print("Json decode failed.")
        return issue_found
    data = jstr['data']

    if 'signed' not in data.keys():
        issue_found += 1
        print("Json decode signed field failed.")
        return issue_found
    if not data['signed']:
        print("User{} has not signed CLA.".format(user['giteeid']))
        issue_found += 1
    print(">>>>>>>>End user valid check, issue:{}.".format(issue_found))
    return issue_found


def member_check(team, token):
    '''
    check tutor information is valid or not.
    :param tutorinfo:
    :return:
    '''
    print(">>>>>>begin member check.")
    issue_found = 0
    membersinfo = team['members']
    for member in membersinfo:
        if 'giteeid' not in member.keys():
            continue
        if 'email' not in member.keys():
            continue
        issue_found += repo_member_valid_check(member, token)
    print(">>>>>>end member check, issue:{}.".format(issue_found))
    return issue_found


def tutor_check(team, token):
    '''
    check tutor information is valid or not.
    :param tutorinfo:
    :return:
    '''
    print(">>>>>>begin tutor check.")
    issue_found = 0
    tutorsinfo = team['tutor']
    for tutor in tutorsinfo:
        if 'giteeid' not in tutor.keys():
            continue
        if 'email' not in tutor.keys():
            continue
        issue_found += repo_member_valid_check(tutor, token)
    print(">>>>>>end tutor check, issue:{}.".format(issue_found))
    return issue_found


def teamid_valid_check(team, legalids):
    '''
    :param team: team information
    :param legalids: legal team ids
    :return:
    '''
    print(">>>>>>begin teamid check.")
    issue_found = 0
    if team['teamid'] not in legalids:
        print("Team id:{} is not in legal team id list.", team['teamid'])
        issue_found += 1
    print(">>>>>>end teamid check, issue:{}.".format(issue_found))
    return issue_found


def teamid_reused_check(teamids):
    '''
    check id reused or not.
    :param teamids:
    :return:
    '''
    print(">>>>Begin teamid reused check.")
    issue_found = 0
    if len(teamids) != len(set(teamids)):
        issue_found += 1
    print(">>>>End teamid reused check, issue:{}.".format(issue_found))
    return issue_found

def orgrepo_reused_check(repos):
    '''
    check repo name reused or not.
    :param repos:repository name set
    :return:
    '''
    print(">>>>Begin repo reused check.")
    issue_found = 0
    if len(repos) != len(set(repos)):
        issue_found += 1
    print(">>>>End repo reused check, issue:{}.".format(issue_found))
    return issue_found


def validaty_check_teaminfo(teams, token, legalids):
    '''
    check team info valid.
    :param teaminfo: team information.
    :param legalids: legal team ids list.
    :return: pass check return 0, else return issue count.
    '''
    print(">>Begin teaminfo check.")
    issue_found = 0

    team_ids = []
    org_repos = []
    for team in teams:
        issue_found += team_has_keyfield(team)
        issue_found += teamid_valid_check(team, legalids)
        issue_found += tutor_check(team, token)
        issue_found += member_check(team, token)

        if issue_found == 0:
            team_ids.append(team['teamid'])
            org_repos.append(team['repository'])
    '''
    team id, name, repositories reused check
    '''
    issue_found += teamid_reused_check(team_ids)
    issue_found += orgrepo_reused_check(org_repos)
    print(">>End teaminfo check, issue:{}.".format(issue_found))
    return issue_found


def validaty_check_version(version):
    '''
    :param version: configure file version, current version 1.0
    :return: version equal 1.0 return 0, else return 1
    '''
    print(">>Begin version check.")
    issue_found = 0
    if version != 1.0:
        print("Version {} is not OK.".format(version))
        issue_found = 1
    print(">>End version check, issue:{}".format(issue_found))
    return issue_found


def validaty_check_community(community, token):
    '''
    :param community: configure file community, current value: openeuler2020
    :return: community equal 'openeuler2020' return 0, else return 1
    '''
    print(">>Begin community check.")
    issue_found = 0
    if community != 'openeuler2020':
        print("Community info{} is not correct.".format(community))
        issue_found += 1

    orgurl = ORG_API + community
    param = {'access_token': token}
    response = requests.get(orgurl, params=param)
    if response.status_code != 200:
        print("Get organization {} information failed.".format(community))
        issue_found += 1
    print(">>End community check, issue:{}.".format(issue_found))
    return issue_found


def load_yaml(directory, yaml_file):
    """
    Helper for load YAML database
    """
    yaml_path = os.path.expanduser(os.path.join(directory, yaml_file))
    try:
        result = yaml.load(
            open(
                yaml_path,
                encoding="utf-8"),
            Loader=yaml.Loader)
    except FileNotFoundError:
        print("Cannot Load %s." % (yaml_path))
        print("Could be wrong path")
        sys.exit(1)
    except yaml.scanner.ScannerError as error:
        print("%s: Invalid YAML file" % (yaml_path))
        print("Detailed Error Information:")
        print(error)
        sys.exit(1)
    return result


def main():
    '''
    This is a main function entry
    '''
    par = argparse.ArgumentParser()
    par.add_argument(
        "managerepo",
        type=str,
        help="Local path of competition manage info repository.")
    par.add_argument(
        "cfgtoken",
        type=str,
        help="Config repo User token ID information.")
    args = par.parse_args()
    cfgtoken = args.cfgtoken
    data = load_yaml(args.managerepo, TEAMINFO)
    legal_ids = load_yaml(args.managerepo, LEGALIDS)

    version = data["version"]
    community = data["community"]
    url = data["giteeurl"]
    teams = data["teams"]

    print("FileVersion:{},\nCommunity:{},\nUrl:{},\nTeam0:{},\n LegalIds:{}.".format(version,
                 community, url, teams[0], legal_ids['legal_team_ids'][0]))
    issue_total = 0

    issue_total += validaty_check_version(version)
    issue_total += validaty_check_community(community, cfgtoken)
    issue_total += validaty_check_teaminfo(teams,
                                           cfgtoken,
                                           legal_ids['legal_team_ids'])

    if issue_total != 0:
        print("CI FAILED, issue count:{}".format(issue_total))
        sys.exit(issue_total)

    print("FINISH")

if __name__ == '__main__':
    main()
