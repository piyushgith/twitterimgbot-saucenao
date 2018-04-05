import tweepy
import random # +146% to sneaking from twatter bot policy
from time import sleep # +1000% to sneaking
from sys import argv
from pyfiglet import Figlet
import argparse
import config

''' this script searches tweets with desired hashtag, likes them(optional) and follows author '''


def main():
    '''runs autofollow addon'''
    unfollow_arg = argument_parser(argv[1:]).u
    fi = Figlet(font='slant')
    print(fi.renderText('''autofollow'''),'\n\nlogging in..') #print welcome message
    global api
    api = config.api
    me = api.me()
    followers_array = []
    for page in tweepy.Cursor(api.followers_ids, id=me.id).pages():
        followers_array.extend(page)
    following_array = []
    for page in tweepy.Cursor(api.friends_ids, id=me.id).pages():
        following_array.extend(page)
    following_counter = len(following_array)

    print('\nwelcome, @' + me.screen_name + '!\n\nfollowers:',len(followers_array),'\nfollowing:',len(following_array),'\n\nsearching for tweets with',config.search_phrase,'and following authors with > ',config.min_followers,'followers')
    if config.like_opt:
        print('\nlike every found tweet option enabled!')
    if config.followback_opt:
        print('\nfollow those who already follows you option enabled!')

    while True:
        stop_code = 'normal'
        following_now_counter = 1
        if not unfollow_arg:
            stop_code,following_now_counter = follow_subroutine(followers_array, following_counter, config.search_phrase, int(config.custom_following_limit), bool(config.followback_opt), bool(config.like_opt))
        if stop_code == 'custom_following_limit_hit':
            break
        if unfollow_arg or stop_code == 'following_hardlimit_hit':
            if not bool(config.unfollow_opt):
                print('unfollowing subroutine disabled in settings! this script cant follow more people')
                break
            else:
                unfollow_subroutine(following_array,followers_array,int(config.custom_unfollowing_limit),following_now_counter)
        if stop_code == 'restart':
            stop_code,following_now_counter = follow_subroutine(followers_array, following_counter, config.search_phrase, int(config.custom_following_limit), bool(config.followback_opt), bool(config.like_opt))

    print('\nmission completion! this script will close in 5 sec..')
    sleep(5)


def follow_subroutine(followers_array, following_counter, search_phrase, custom_following_limit, followback_opt, like_opt):
    '''finds tweets and follows author (and likes tweet if set)'''
    print('\nstarting following subroutine..')
    following_now_counter = 0
    with open(config.autofollow_log_file, 'r') as log_file: #get array of users who we followed from log
        already_followed_array = log_file.readlines()
    for twit in tweepy.Cursor(api.search, q=search_phrase).items():
        if following_counter >= custom_following_limit:
                print('\ncustom following limit hit! stopping following subroutine...')
                return 'custom_following_limit_hit', following_now_counter
        sleep_time = 1+5*random.random()
        if following_counter >= random.randint(4977,4999):
            if following_counter >= len(followers_array) - random.randint(-500,50):
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit:',len(followers_array),'\nsleeping',sleep_time,'sec before next step to avoid detection..\n')
                sleep(sleep_time)
                return 'following_hardlimit_hit',following_now_counter
            if len(followers_array) <= 5000:
                print('\nfollowing subroutine stopped, you are too close to twitter following hardlimit: 5000\nsleeping',sleep_time,'sec before next step to avoid detection..\n')
                sleep(sleep_time)
                return 'following_hardlimit_hit',following_now_counter
        try:
            userid = twit.user.id
            print('\nfound tweet by user id',userid)
            if userid in followers_array and not followback_opt:
                print('this user already follows us..')
                sleep(random.random())
            else:
                if str(userid) in already_followed_array:
                    print('already tried to follow this user..')
                    sleep(random.random())
                else:
                    if twit.user.following:
                        print('already following this user(not by script)..')
                        sleep(random.random())
                    else:
                        dood_followers_count = twit.user.followers_count
                        dood_following_count = twit.user.friends_count
                        if dood_following_count > dood_followers_count - dood_followers_count*0.1 and dood_following_count < 2*dood_followers_count and dood_followers_count > config.min_followers:
                            twit.user.follow()
                            following_now_counter += 1
                            following_counter += 1  # real following counter
                            print('followed this user, total following:',following_counter,'followed now:',following_now_counter,'\nsleeping',sleep_time,'sec to avoid detection..')
                            if like_opt:
                                twit.favorite()
                                print('liked this tweet')
                            sleep(sleep_time)
                        else:
                            if dood_following_count < dood_followers_count - dood_followers_count*0.1:
                                print('.doesnt seems like mutual')
                            if dood_following_count > 2*dood_followers_count:
                                print('.follows more than 2x his followers, obviously bot')
                            if dood_followers_count < config.min_followers:
                                print('.doesnt have enough followers')
                            sleep(0.5+random.random())
                        already_followed_array.append(userid)
                        with open(config.autofollow_log_file, 'a') as log_file:
                            log_file.write(str(userid) + '\n')
        except tweepy.TweepError as e:
            print('\ntweepy error!\n' + e.reason)
            if '161' in str(e.reason):
                print('\ncode 161 detected! you probably ran out of daily following limit\n\ndo not try to follow more people now or u might get banned!\n\nwaiting 10 hours before next try..')
                sleep(10*60*60)
                return 'restart', following_now_counter
        except StopIteration:
            print('\nwe searched all tweets, sleeping 10 minutes before next try..')
            sleep(600)
            return 'restart', following_now_counter
    print('following subroutine crashed for some reason, restarting in',sleep_time,'sec')
    sleep(sleep_time)
    return 'restart', following_now_counter


def unfollow_subroutine(following_array,followers_array,custom_unfollowing_limit,following_now_counter):
    '''unfollows non mutuals (followed by this script only!!) from oldest to newest'''
    print('\nstarting unfollowing subroutine..\nno worries, it will unfollow only non mutuals followed by this script\n')
    unfollowed_count = 0
    unfollowing_candidates = []
    with open(config.autofollow_log_file, 'r') as log_file: #get array of users who we followed from log
        already_followed_array = [line.rstrip('\n') for line in log_file]
    for dood in reversed(following_array):
        if not dood in followers_array and str(dood) in already_followed_array:
            unfollowing_candidates.append(dood)
    print(len(unfollowing_candidates),'candidates for unfollow\n')
    for dood in unfollowing_candidates:
        sleep_time = 1+10*random.random()
        print('user id ',dood, 'followed by this script but didnt followed you back')
        api.destroy_friendship(id=dood)
        unfollowed_count += 1
        print('unfollowed him.. total:',unfollowed_count,'\nsleeping',sleep_time,'sec to avoid detection..\n')
        sleep(sleep_time)
        if unfollowed_count > random.randint(custom_unfollowing_limit - 100, custom_unfollowing_limit) or unfollowed_count >= len(unfollowing_candidates) - following_now_counter:
            sleep_time_long = random.randint(30*60, 120*60)
            print('\nunfollowing subroutine stopped',unfollowing_count,'users was unfollowed\nsleeping',sleep_time_long,' sec before another following cycle to avoid detection..\n')
            sleep(sleep_time_long)
            break


def argument_parser(args):
    '''parsing arguments from command line'''
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', help='start unfollow subroutine first',
                        action='store_true')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
