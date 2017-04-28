#!/usr/bin/python
#
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Creates and publishes changelog post for the spinnaker.github.io site.
#
# 'Publishing' in this case means creating a new file, 'git add'ing it to the
# local git repository for spinnaker.github.io, and then pushing a commit
# to origin/master.
#
# A private key that has access to --githubio_repo needs to be added
# to a running ssh-agent on the machine this script will run on:
#
# > <copy or rsync the key to the vm>
# > eval `ssh-agent`
# > ssh-add ~/.ssh/<key with access to github repos>
#
# If you are running this script on Jenkins, you can configure Jenkins to handle SSH credentials.

import argparse
import datetime
import os
import re
import sys

from spinnaker.run import check_run_quick

# Path to the posts directory in the spinnaker.github.io site.
POSTS_DIR = '_posts'

class ChangelogPublisher():

  def __init__(self, options, changelog_gist_uri=None):
    self.__version = options.version
    self.__githubio_repo_uri = options.githubio_repo_uri
    self.__changelog_gist_uri = changelog_gist_uri or options.changelog_gist_uri

  def __checkout_githubio_repo(self):
    """Clones the spinnaker.github.io git repo.
    """
    check_run_quick('git clone {0}'.format(self.__githubio_repo_uri))

  def __format_changelog_post(self):
    # Initialized with 'front matter' necessary for the post.
    timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
    post_lines = [
      '---',
      'title: Spinnaker Changelog {version}'.format(version=self.__version),
      'date: {date}'.format(date=timestamp),
      'categories: changelogs',
      '---',
      ''
    ]

    # Since we include the changelog gist as a script, make sure we're
    # referring to the gist javascript file.
    if self.__changelog_gist_uri and not self.__changelog_gist_uri.endswith('.js'):
      self.__changelog_gist_uri = self.__changelog_gist_uri + '.js'

    post_lines.append('<script src="{uri}"></script>'.format(uri=self.__changelog_gist_uri))
    post = '\n'.join(post_lines)
    return post

  def __publish_post(self, post_content):
    day = '{:%Y-%m-%d}'.format(datetime.datetime.now())
    post_name = '{day}-{version}-changelog.md'.format(day=day, version=self.__version)
    repo_name = os.path.basename(self.__githubio_repo_uri)

    if repo_name.endswith('.git'):
      repo_name = re.sub('.git$', '', repo_name)

    post_path = os.path.join(repo_name, POSTS_DIR, post_name)
    # Path to post file relative to the git root.
    post_rel_path = os.path.join(POSTS_DIR, post_name)
    with open(post_path, 'w') as post_file:
      post_file.write(post_content)

    check_run_quick('git -C {0} add {1}'.format(repo_name, post_rel_path))
    message = 'Changelog for version {0} auto-generated by {1}'.format(self.__version, __file__)
    check_run_quick('git -C {0} commit -m "{1}"'.format(repo_name, message))
    check_run_quick('git -C {0} push origin master'.format(repo_name))

  def publish_changelog(self):
    self.__checkout_githubio_repo()
    post = self.__format_changelog_post()
    self.__publish_post(post)

  @classmethod
  def init_argument_parser(cls, parser):
    """Initialize command-line arguments."""
    parser.add_argument('--githubio_repo_uri', default='', required=True,
                        help='The ssh uri of the spinnaker.github.io repo to'
                        'commit the changelog post to, e.g. git@github.com:spinnaker/spinnaker.github.io.')
    parser.add_argument('--version', default='', required=True,
                        help='The version of Spinnaker that corresponds to the changelog.')
    parser.add_argument('--changelog_gist_uri', default='',
                        help='A uri that points to a gist containing the changelog.')

  @classmethod
  def main(cls):
    parser = argparse.ArgumentParser()
    cls.init_argument_parser(parser)
    options = parser.parse_args()

    result_publisher = cls(options)
    result_publisher.publish_changelog()

if __name__ == '__main__':
  sys.exit(ChangelogPublisher.main())
