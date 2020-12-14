
'''
This is a bot for openEuler competition repository manage.
'''

import argparse
import yaml
import os
import sys
import requests

TEAMINFO = "TEAM_INFO/teaminfo.yaml"
LEGALIDS = "TEAM_INFO/legalids.yaml"
COMMUNITY = "openeuler2020"
ORG_API = "https://gitee.com/api/v5/orgs/"
USER_API = "https://gitee.com/api/v5/users/"
CLA_API = "https://clasign.osinfra.cn/api/v1/individual-signing/gitee/openeuler"
REPO_API = "https://gitee.com/api/v5/repos/"


def add_repo_member(team, community, orgtoken):
    '''
    add members for the repository
    :param team:
    :param community:
    :param orgtoken:
    :return:
    '''
    member_url = REPO_API + community + '/' + \
        team['repository'] + '/collaborators/'
    user = team['members'] + team['tutor']
    for member in user:
        member_url = member_url + member['giteeid']
        param = {'access_token': '679918f879a12d327058af1e76a09c90',
                 'permission': 'push'}
        response = requests.put(member_url, params=param)
        if response.status_code != 200:
            print(
                "Add repo member:{} to repo:{} failed.".format(
                    member['giteeid'],
                    team['repository']))
            continue
    return


def create_team_repo(team, community, orgtoken):
    '''
    create a team repository.
    :param repo:
    :param community:
    :param orgtoken:
    :return:
    '''

    repo_url = ORG_API + community + '/repos'
    param = {'access_token': orgtoken,
             'name': team['repository'],
             'description': team['description'],
             'has_issues': 'true',
             'has_wiki': 'true',
             'can_comment': 'true',
             'private': 'true' if team['repotype'] == 'private' else 'false',
             'auto_init': 'true'}
    response = requests.post(repo_url, params=param)
    if response.status_code != 201:
        print(
            "Create repo {} on gitee failed.".format(team['repository']))
        return False

    return True


def check_repo_exist(repo, community, orgtoken):
    '''
    check if there is a same repo exist.
    :param repo:
    :param community:
    :param orgtoken:
    :return:
    '''
    repo_url = REPO_API + community + '/' + repo
    param = {'access_token': orgtoken}
    response = requests.get(repo_url, params=param)
    if response.status_code == 200:
        print(
            "Get repo {} from gitee success.".format(repo))
        return True

    return False


def check_and_create_teamrepo(teams, community, orgtoken):
    '''
    to check if there is a repo, or create it.
    :param team:
    :param token:
    :return:
    '''
    for team in teams:
        repo_exist = check_repo_exist(team['repository'], community, orgtoken)
        if repo_exist:
            continue
        ret = create_team_repo(team, community, orgtoken)
        if not ret:
            continue
        add_repo_member(team, community, orgtoken)

    return


def team_has_keyfield(team):
    issue_found = 0
    if 'teamid' not in team.keys() or len(team['teamid']) == 0:
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
    issue_found = 0
    '''
    check user gitee id valid
    '''
    user_url = USER_API + user['giteeid']
    param = {'access_token': token}
    response = requests.get(user_url, params=param)
    if response.status_code != 200:
        print(
            "Get User {} information from gitee failed.".format(
                user['giteeid']))
        issue_found += 1
        return
    '''
    check user cla sign.
    '''
    cla_url = CLA_API
    param = {'email': user['email']}
    response = requests.get(user_url, params=param)
    if response.status_code != 200:
        print("Get User{} cla info failed.".format(user['giteeid']))
        issue_found += 1
        return issue_found
    if not response.data.signed:
        print("User{} has not signed CLA.".format(user['giteeid']))
        issue_found += 1

    return issue_found


def member_check(team, token):
    '''
    check tutor information is valid or not.
    :param tutorinfo:
    :return:
    '''
    issue_found = 0
    membersinfo = team['members']
    for member in membersinfo:
        issue_found += repo_member_valid_check(member, token)

    return issue_found


def tutor_check(team, token):
    '''
    check tutor information is valid or not.
    :param tutorinfo:
    :return:
    '''
    issue_found = 0
    tutorsinfo = team['tutor']
    for tutor in tutorsinfo:
        issue_found += repo_member_valid_check(tutor, token)

    return issue_found


def teamid_valid_check(team, legalids):
    '''
    :param team: team information
    :param legalids: legal team ids
    :return:
    '''
    issue_found = 0
    if team['teamid'] not in legalids:
        issue_found += 1
    return issue_found


def teamid_reused_check(teamids):
    '''
    check id reused or not.
    :param teamids:
    :return:
    '''
    issue_found = 0
    if len(teamids) != len(set(teamids)):
        issue_found += 1
    return issue_found


def teamname_reused_check(teamnames):
    '''
    check name reused or not.
    :param teamnames:
    :return:
    '''
    issue_found = 0
    if len(teamnames) != len(set(teamnames)):
        issue_found += 1
    return issue_found


def orgrepo_reused_check(repos):
    '''
    check repo name reused or not.
    :param repos:repository name set
    :return:
    '''
    issue_found = 0
    if len(repos) != len(set(repos)):
        issue_found += 1
    return issue_found


def validaty_check_teaminfo(teams, token, legalids):
    '''
    check team info valid.
    :param teaminfo: team information.
    :param legalids: legal team ids list.
    :return: pass check return 0, else return issue count.
    '''
    issue_found = 0

    team_ids = []
    team_names = []
    org_repos = []
    for team in teams:
        issue_found += team_has_keyfield(team)
        issue_found += teamid_valid_check(team, legalids)
        issue_found += tutor_check(team, token)
        issue_found += member_check(team, token)

        if issue_found == 0:
            team_ids.append(team['teamid'])
            team_names.append(team['teamname'])
            org_repos.append(team['repository'])
    '''
    team id, name, repositories reused check
    '''
    issue_found += teamid_reused_check(team_ids)
    issue_found += teamname_reused_check(team_names)
    issue_found += orgrepo_reused_check(org_repos)

    return issue_found


def validaty_check_version(version):
    '''
    :param version: configure file version, current version 1.0
    :return: version equal 1.0 return 0, else return 1
    '''
    issue_found = 0
    if version != 1.0:
        print("Version {} is not OK.".format(version))
        issue_found = 1
    return issue_found


def validaty_check_community(community, token):
    '''
    :param community: configure file community, current value: openeuler2020
    :return: community equal 'openeuler2020' return 0, else return 1
    '''
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
    par.add_argument(
        "orgtoken",
        type=str,
        help="Organization repo User token ID information.")
    args = par.parse_args()
    cfgtoken = args.cfgtoken
    orgtoken = args.orgtoken
    data = load_yaml(args.managerepo, TEAMINFO)
    legal_ids = load_yaml(args.managerepo, LEGALIDS)

    version = data["version"]
    community = data["community"]
    url = data["giteeurl"]
    teams = data["teams"]

    issue_total = 0

    issue_total += validaty_check_version(version)
    issue_total += validaty_check_community(community, cfgtoken)
    issue_total += validaty_check_teaminfo(teams,
                                           cfgtoken,
                                           legal_ids['legal_team_ids'])

    if issue_total != 0:
        sys.exit(issue_total)

    '''
    begin to create repository
    '''
    check_and_create_teamrepo(teams, community, orgtoken)

    print(
        "Token {},\nFileVersion:{},\nCommunity:{},\nUrl:{},\nTeam0:{},\n LegalIds:{}.".format(
            cfgtoken,
            version,
            community,
            url,
            teams[0],
            legal_ids['legal_team_ids'][0]))


if __name__ == '__main__':
    main()
