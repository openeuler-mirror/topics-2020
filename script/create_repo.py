
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
        user_url = member_url + member['giteeid']
        param = {'access_token': orgtoken,
                 'permission': 'push'}
        response = requests.put(user_url, params=param)
        if response.status_code != 200:
            print("Add repo member:{} to repo:{} failed, ret:{}.".format(
                    member['giteeid'],
                    team['repository'],
                    response.status_code))
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
        print("Get repo {} from gitee success.".format(repo))
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
            add_repo_member(team, community, orgtoken)
            continue
        ret = create_team_repo(team, community, orgtoken)
        if not ret:
            continue
        add_repo_member(team, community, orgtoken)

    return


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
        "orgtoken",
        type=str,
        help="Organization repo User token ID information.")
    args = par.parse_args()
    orgtoken = args.orgtoken
    data = load_yaml(args.managerepo, TEAMINFO)
    legal_ids = load_yaml(args.managerepo, LEGALIDS)

    version = data["version"]
    community = data["community"]
    url = data["giteeurl"]
    teams = data["teams"]

    '''
    begin to create repository
    '''
    check_and_create_teamrepo(teams, community, orgtoken)


if __name__ == '__main__':
    main()
