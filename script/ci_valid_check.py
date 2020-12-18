
'''
This is a bot for openEuler competition repository manage.
'''

import argparse
import yaml
import os
import sys
import requests
import json
from collections import defaultdict
from collections import Counter


TEAMINFO = "TEAM_INFO/teaminfo.yaml"
LEGALIDS = "TEAM_INFO/legalids.yaml"
COMMUNITY = "openeuler2020"
ORG_API = "https://gitee.com/api/v5/orgs/"
USER_API = "https://gitee.com/api/v5/users/"
CLA_API = "https://clasign.osinfra.cn/api/v1/individual-signing/gitee/openeuler"
TAG_API = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}/labels"
LOCAL_REPO = "topics-2020"
LOCAL_COMMUNITY = "openeuler-competition"
COMMENT_API = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}/comments"
TWO_COL_COMMENT = "<tr> <th>Item</th> <th>Check Result</th> </tr>"
THREE_COL_COMMENT = "<tr> <th>Item</th> <th>ID</th>  <th>Check Result</th> </tr>"
PASS = ":white_check_mark:PASS"
FAIL = ":x:FAIL"


def gen_repo_name(topicid, teamname):
    return "{}-{}".format(topicid, teamname)

def send_comment_checkret(pr, token, comment_data):
    table_head = '<table>'
    table_tail = '</table>'
    global COMMENT
    comment = table_head + comment_data + table_tail
    comment_url = COMMENT_API.format(LOCAL_COMMUNITY, LOCAL_REPO, pr)
    pydata = {"access_token": token, "body": comment}
    headers = {'Content-Type': 'application/json'}
    rsp = requests.post(comment_url, headers=headers, data=json.dumps(pydata))
    if rsp.status_code != 201:
        print(comment_url)
        print("Send comment to pr:{} failed:{}.".format(pr, rsp.status_code))
    return

def add_2col_comment_item(item):
    global TWO_COL_COMMENT
    TWO_COL_COMMENT += item
    return

def add_3col_comment_item(item):
    global THREE_COL_COMMENT
    THREE_COL_COMMENT += item
    return


def version_comment(result):
    ver_comment = "<tr> <td>Version</td> <td> {} </td> </tr>"
    if result:
        ver_comment = ver_comment.format(PASS)
    else:
        ver_comment = ver_comment.format(FAIL)
    print(ver_comment)
    add_2col_comment_item(ver_comment)
    return

def community_comment(result):
    commu_comment = "<tr> <td>Community</td> <td> {} </td> </tr>"
    if result:
        commu_comment = commu_comment.format(PASS)
    else:
        commu_comment = commu_comment.format(FAIL)
    print(commu_comment)
    add_2col_comment_item(commu_comment)
    return

def integrity_comment(result):
    integrity_comment = "<tr> <td>IntegrityCheck</td> <td> {} </td> </tr>"
    if result:
        integrity_comment = integrity_comment.format(PASS)
    else:
        integrity_comment = integrity_comment.format(FAIL)
    add_2col_comment_item(integrity_comment)
    return

def teamid_comment(team_info):
    cnt = len(team_info)
    first_col = "<td rowspan={}>TeamID check</td>".format(cnt)
    teamid_comm = "<tr> {} <td>{}</td> <td>{}</td> </tr>"
    comment = ""
    is_first = True 
    for key in team_info.keys():
        ret = PASS if team_info[key] else FAIL
        if is_first:
            comment += teamid_comm.format(first_col, key, ret)
            is_first = False
        else:
            comment += teamid_comm.format("", key, ret)
    print(comment)
    add_3col_comment_item(comment)
    return


def user_comment(user_info):
    cnt = len(user_info)
    if cnt == 0:
        return
    first_col = "<td rowspan={}>GiteeID check</td>".format(cnt)
    user_comm = "<tr> {} <td>{}</td> <td>{}</td> </tr>"
    comment = ""
    is_first = True
    for key in user_info.keys():
        ret = PASS if user_info[key] else FAIL
        if is_first:
            comment += user_comm.format(first_col, key, ret)
            is_first = False
        else:
            comment += user_comm.format("", key, ret)
    add_3col_comment_item(comment)
    return


def cla_comment(clasign_info):
    cnt = len(clasign_info)
    if cnt == 0:
        return
    first_col = "<td rowspan={}>CLA_SIGN check</td>".format(cnt)
    cla_comm = "<tr> {} <td>{}</td> <td>{}</td> </tr>"
    comment = ""
    is_first = True
    for key in clasign_info.keys():
        ret = PASS if clasign_info[key] else FAIL
        if is_first:
            comment += cla_comm.format(first_col, key, ret)
            is_first = False
        else:
            comment += cla_comm.format("", key, ret)
    add_3col_comment_item(comment)
    return

def repo_comment(repos_info):
    cnt = len(repos_info)
    if cnt == 0:
        return
    first_col = "<td rowspan={}>Repository check</td>".format(cnt)
    reponame_comm = "<tr> {} <td>{}</td> <td>{}</td> </tr>"
    comment = ""
    is_first = True
    for key in repos_info.keys():
        ret = PASS if repos_info[key] else FAIL
        if is_first:
            comment += reponame_comm.format(first_col, key, ret)
            is_first = False
        else:
            comment += reponame_comm.format("", key, ret)
    add_3col_comment_item(comment)
    return


def delete_gitee_tag(pr, tag, token):
    '''
    delete gitee tag
    :param pr:
    :param tags:
    :return:
    '''
    print("Being to delete tag:{} for pr:{}.".format(tag ,pr))
    if not tag:
        print("Tag is none.")
        return
    pr_tag_url = TAG_API.format(LOCAL_COMMUNITY, LOCAL_REPO, pr)
    pr_tag_url = pr_tag_url + "/" + tag
    param = {'access_token': token}
    response = requests.delete(pr_tag_url, params=param, timeout=10)
    if response.status_code != 204:
        print("Delete tag:{} at pr:{} in repo:{} community:{} failed.".format(tag, pr, LOCAL_REPO, LOCAL_COMMUNITY))
    print("End to delete tag:{}".format(tag))
    return


def add_gitee_tag(pr, tag, token):
    """
    add gitee tag
    :param pr:
    :param tags:
    :return:
    """
    print("Being to add tag for pr:{}.".format(pr))
    if not tag:
        print("Tags are none.")
        return True
    pr_tag_url = TAG_API.format(LOCAL_COMMUNITY, LOCAL_REPO, pr)
    pr_tag_url = pr_tag_url + "?access_token=" + token
    labels = "[\"{}\"]".format(tag)
    response = requests.post(pr_tag_url, data=labels, timeout=10)
    if response.status_code != 201:
        print("Add tags:{} to community:{} repo:{}, failed:{}.".format(tag, LOCAL_COMMUNITY, LOCAL_REPO, response.status_code))
        return False
    print("End add tag:{} for pr:{}.".format(tag, pr))
    return True


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
    if 'topicid' not in team.keys() :
        print("There is no topic id in teaminfo.")
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
    user_issue = 0
    cla_issue = 0
    '''
    check user gitee id valid
    '''
    user_url = USER_API + user['giteeid']
    param = {'access_token': token}
    response = requests.get(user_url, params=param)
    if response.status_code != 200:
        print("Get User {} information from gitee failed.".format(user['giteeid']))
        user_issue += 1
    '''
    check user cla sign.
    '''
    param = {'email': user['email']}
    response = requests.get(CLA_API, params=param)
    if response.status_code != 200:
        print("Get User:{} cla info failed.".format(user['giteeid']))
        cla_issue += 1
        return user_issue, cla_issue

    jstr = json.loads(response.text)
    if 'data' not in jstr.keys():
        cla_issue += 1
        print("Json decode failed.")
        return user_issue, cla_issue
    data = jstr['data']

    if 'signed' not in data.keys():
        cla_issue += 1
        print("Json decode signed field failed.")
        return user_issue, cla_issue
    if not data['signed']:
        print("User{} has not signed CLA.".format(user['giteeid']))
        cla_issue += 1
    print(">>>>>>>>End user valid check, issue:{}.".format(user_issue + cla_issue))
    return user_issue, cla_issue


def member_check(team, token, user_info, cla_info):
    '''
    check tutor information is valid or not.
    :param tutorinfo:
    :return:
    '''
    print(">>>>>>begin member check.")
    user_issue = 0
    cla_issue = 0

    membersinfo = team['members']
    for member in membersinfo:
        if 'giteeid' not in member.keys():
            continue
        if 'email' not in member.keys():
            continue
        user_issue, cla_issue = repo_member_valid_check(member, token)
        user_info[member['giteeid']] = user_info[member['giteeid']] and (user_issue == 0)
        cla_info[member['email']] = cla_info[member['email']] and (cla_issue == 0)
    print(">>>>>>end member check, issue:{}.".format(user_issue + cla_issue))
    return user_issue, cla_issue


def tutor_check(team, token, user_info, cla_info):
    '''
    check tutor information is valid or not.
    :param tutorinfo:
    :return:
    '''
    print(">>>>>>begin tutor check.")
    user_issue = 0
    cla_issue = 0

    tutorsinfo = team['tutor']
    for tutor in tutorsinfo:
        if 'giteeid' not in tutor.keys():
            continue
        if 'email' not in tutor.keys():
            continue
        user_issue, cla_issue = repo_member_valid_check(tutor, token)
        user_info[tutor['giteeid']] = user_info[tutor['giteeid']] and (user_issue == 0)
        cla_info[tutor['email']] = cla_info[tutor['email']] and (cla_issue == 0)

    print(">>>>>>end tutor check, issue:{}.".format(user_issue + cla_issue))
    return user_issue, cla_issue


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
    ids = []
    if len(teamids) != len(set(teamids)):
        ids = [item for item, count in Counter(teamids).items() if count > 1]
        issue_found += 1
    print(">>>>End teamid reused check, issue:{}.".format(issue_found))

    return issue_found, ids

def orgrepo_reused_check(repos):
    '''
    check repo name reused or not.
    :param repos:repository name set
    :return:
    '''
    print(">>>>Begin repo reused check.")
    issue_found = 0
    reponames = []
    if len(repos) != len(set(repos)):
        reponames = [item for item, count in Counter(repos).items() if count > 1]
        issue_found += 1
    print(">>>>End repo reused check, issue:{}.".format(issue_found))
    return issue_found, reponames


def validaty_check_teaminfo(teams, token, legalids):
    '''
    check team info valid.
    :param teaminfo: team information.
    :param legalids: legal team ids list.
    :return: pass check return 0, else return issue count.
    '''
    print(">>Begin teaminfo check.")
    issue_found = 0

    integrity_issue = 0

    teamid_issue = 0
    teamid_info = defaultdict(lambda: True)

    repo_issue = 0
    repo_info = defaultdict(lambda: True)

    user_issue = 0
    user_info = defaultdict(lambda: True)

    cla_issue = 0
    cla_info = defaultdict(lambda: True)

    team_ids = []
    org_repos = []
    for team in teams:
        integrity_issue = team_has_keyfield(team)
        issue_found += integrity_issue

        teamid_issue = teamid_valid_check(team, legalids)
        teamid_info[team['teamid']] = teamid_info[team['teamid']] and (teamid_issue == 0)
        issue_found += teamid_issue

        user_issue, cla_issue = tutor_check(team, token, user_info, cla_info)
        issue_found += (user_issue + cla_issue)

        user_issue, cla_issue = member_check(team, token, user_info, cla_info)
        issue_found += (user_issue + cla_issue)

        team_ids.append(team['teamid'])
        org_repos.append(gen_repo_name(team['topicid'], team['teamname']))
        repo_info[gen_repo_name(team['topicid'], team['teamname'])] = True
    '''
    team id, name, repositories reused check
    '''
    teamid_issue, teamids = teamid_reused_check(team_ids)
    if teamid_issue != 0:
        for id in teamids:
            teamid_info[id] = False
    issue_found += teamid_issue

    repo_issue, reponames = orgrepo_reused_check(org_repos)
    if repo_issue != 0:
        for name in reponames:
            repo_info[name] = False
    issue_found += repo_issue
    print(">>End teaminfo check, issue:{}.".format(issue_found))

    '''
    add comment
    '''
    integrity_comment(integrity_issue == 0)
    teamid_comment(teamid_info)
    repo_comment(repo_info)
    user_comment(user_info)
    cla_comment(cla_info)
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
        "prnumber",
        type=int,
        help="The PR number.")
    par.add_argument(
        "cfgtoken",
        type=str,
        help="Config repo User token ID information.")
    args = par.parse_args()
    cfgtoken = args.cfgtoken
    pr = args.prnumber
    data = load_yaml(args.managerepo, TEAMINFO)
    legal_ids = load_yaml(args.managerepo, LEGALIDS)

    version = data["version"]
    community = data["community"]
    url = data["giteeurl"]
    teams = data["teams"]

    issue_total = 0

    version_issue = validaty_check_version(version)
    version_comment(version_issue == 0)
    issue_total += version_issue

    community_issue = validaty_check_community(community, cfgtoken)
    community_comment(community_issue == 0)
    issue_total += community_issue

    issue_total += validaty_check_teaminfo(teams,
                                           cfgtoken,
                                           legal_ids['legal_team_ids'])

    if issue_total != 0:
        print("CI FAILED, issue count:{}".format(issue_total))
        delete_gitee_tag(pr,"ci_successful", cfgtoken)
        add_gitee_tag(pr, "ci_failed", cfgtoken)
        send_comment_checkret(pr, cfgtoken, TWO_COL_COMMENT)
        send_comment_checkret(pr, cfgtoken, THREE_COL_COMMENT)
        sys.exit(issue_total)

    delete_gitee_tag(pr,"ci_failed", cfgtoken)
    add_gitee_tag(pr, "ci_successful", cfgtoken)
    send_comment_checkret(pr, cfgtoken, TWO_COL_COMMENT)
    send_comment_checkret(pr, cfgtoken, THREE_COL_COMMENT)
    print("FINISH")

if __name__ == '__main__':
    main()
