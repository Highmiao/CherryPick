import argparse
import colorama
from colorama import Fore
from git import Repo, GitCommandError
colorama.init(autoreset=True)

def print_commit_diff(repo, file, branch1, branch2):
    diff = repo.git.diff(branch1, branch2, '--', file)
    if diff:
        print(f"{Fore.RED}{diff}")  # 使用 colorama 来添加红色
    else:
        print("No differences found.")

def list_conflicted_files(repo):
    # 由于 GitPython 可能不直接提供冲突文件的清单，我们可以通过检查状态来获取
    conflicted_files = []
    for item in repo.index.diff("HEAD"):
        if item.change_type == 'U':
            conflicted_files.append(item.a_path)
    return conflicted_files

def print_history(repo, branch, file):
    commits = list(repo.iter_commits(branch, paths=file))
    for commit in commits:
        print(f"Commit: {commit.hexsha}")
        print(f"Author: {commit.author.name}")
        print(f"Date: {commit.committed_datetime}")
        print(f"Message: {commit.message}")
        print("-" * 50)

# 创建ArgumentParser对象
parser = argparse.ArgumentParser(description='Cherry-pick commits from one branch to another based on a pattern.')

# 添加分支名和模式的命令行参数
parser.add_argument('branch_from', help='Name of the source branch')
parser.add_argument('branch_to', help='Name of the target branch')
parser.add_argument('pattern', help='Pattern to search in commit messages')

# 解析命令行参数
args = parser.parse_args()

# 路径到你的仓库
repo_path = 'D:\Projects\CherryPickConflict'
# 分支名称
branch_a = args.branch_from
branch_b = args.branch_to
# 提交信息中要搜索的模式
pattern = args.pattern

repo = Repo(repo_path)

# 确保工作目录是干净的
assert not repo.is_dirty(), "Repository has uncommitted changes."

# 切换到目标分支，比如master或main，这里以main为例
repo.git.checkout('beta')

# 获取两个分支之间的差异提交
commits = list(repo.iter_commits(f'{branch_b}..{branch_a}'))

# 筛选出消息符合特定模式的提交
filtered_commits = [commit for commit in commits if pattern in commit.message]

# 尝试cherry-pick每个符合条件的提交
for commit in reversed(filtered_commits):
    try:
        repo.git.cherry_pick(commit.hexsha)
        print(f"Cherry-picking commit {commit.message} {commit.hexsha} succeed")
    except GitCommandError as e:
        print(f"{Fore.RED}Cherry-picking commit {commit.message} {commit.hexsha} failed")
        conflicted_files = list_conflicted_files(repo)
        for file in conflicted_files:
            print(f"{Fore.YELLOW}Conflicts in file: {file}")
            print("Current branch commit history:")
            print_history(repo, branch_b, file)
            print("=" * 50)
            print("Target branch commit history:")
            print_history(repo, branch_a, file)
            print("Differences in commit history:")
            print_commit_diff(repo, file, branch_b, branch_a)
        repo.git.cherry_pick('--abort')
        break

