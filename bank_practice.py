# -*- coding: utf-8 -*-
"""
驾考题库刷题工具
"""

import json
import os
import sys
import random
import re
import html
import hashlib
import webbrowser
import urllib.request
import subprocess
from pathlib import Path

# ===== 路径与常量配置 =====
BASE_DIR = Path(__file__).resolve().parent
BANK_PATH = BASE_DIR / "Question-Bank.json"
LOG_PATH = BASE_DIR / "bank_log.json"
CACHE_DIR = BASE_DIR / ".bank_img_cache"

# 题型常量
TYPE_SINGLE = 1
TYPE_MULTI = 2
TYPE_JUDGE = 3
TYPE_NAMES = {1: "单选题", 2: "多选题", 3: "判断题"}

# 模拟考试配置：科目 -> (题数, 每题分值, 合格分)
EXAM_CONFIG = {
    1: {"count": 100, "per_score": 1, "pass_score": 90,
        "judge": 40, "single": 60, "multi": 0},
    4: {"count": 50, "per_score": 2, "pass_score": 90,
        "judge": 20, "single": 20, "multi": 10},
}


# ===== 工具函数 =====

def strip_html(text):
    """剥离 HTML 标签，保留纯文本。"""
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>\s*', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return text.strip()


def normalize_answer(raw):
    """将用户输入归一化为排序后的大写字母串"""
    s = raw.strip().upper()
    s = s.replace('，', ',').replace(' ', '')
    # 判断题快捷输入
    if s in ('对', '正确', 'T', 'Y', '√', 'A'):
        return 'A'
    if s in ('错', '错误', 'F', 'N', '×', 'B'):
        return 'B'
    # 提取字母
    letters = sorted(set(c for c in s if c in 'ABCDE'))
    return ''.join(letters)


def get_image_cache_path(url):
    """根据 URL 生成本地缓存文件路径，用 URL 哈希避免冲突。"""
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
    # 取原始文件名用于保留扩展名
    tail = url.rsplit('/', 1)[-1].split('?')[0]
    suffix = Path(tail).suffix or '.jpg'
    return CACHE_DIR / f"{url_hash}{suffix}"


def download_image(url):
    """下载图片到缓存目录，返回本地路径；失败返回 None。"""
    if not url:
        return None
    cache_file = get_image_cache_path(url)
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        print("  [正在加载图片...]")
        with urllib.request.urlopen(req, timeout=15) as resp:
            # 分块读取，限制最大 10MB
            chunks = []
            total = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > 10 * 1024 * 1024:
                    return None
                chunks.append(chunk)
            data = b''.join(chunks)
        if not data:
            return None
        with open(cache_file, 'wb') as f:
            f.write(data)
        return cache_file
    except Exception:
        return None


def open_image(path):
    """用系统默认查看器打开本地图片文件。"""
    try:
        if sys.platform == 'win32':
            os.startfile(str(path))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(path)], check=False)
        else:
            subprocess.run(['xdg-open', str(path)], check=False)
    except Exception:
        try:
            webbrowser.open(str(path))
        except Exception:
            pass


def show_image(url):
    """下载并显示题目图片，失败则用浏览器打开 URL。"""
    if not url:
        return
    path = download_image(url)
    if path:
        open_image(path)
    else:
        try:
            webbrowser.open(url)
        except Exception:
            print(f"  [无法显示图片，URL: {url}]")


# ===== 题库与日志管理 =====

def load_bank():
    """加载题库 JSON 文件。"""
    with open(BANK_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_log():
    """加载刷题日志，返回 {done: {id: 次数}, wrong: {id: 次数}}。"""
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"done": {}, "wrong": {}}
    return {"done": {}, "wrong": {}}


def save_log(log):
    """保存刷题日志（原子写入，避免崩溃导致文件损坏）。"""
    tmp_path = LOG_PATH.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        os.replace(str(tmp_path), str(LOG_PATH))
    except Exception as e:
        print(f"  [警告: 保存日志失败: {e}]")


def record_done(log, qid):
    """记录已做题目并立即持久化。"""
    qid = str(qid)
    log['done'][qid] = log['done'].get(qid, 0) + 1
    save_log(log)


def record_wrong(log, qid):
    """记录错题并立即持久化。"""
    qid = str(qid)
    log['wrong'][qid] = log['wrong'].get(qid, 0) + 1
    save_log(log)


def remove_wrong(log, qid):
    """答对后从错题本移除"""
    pass


# ===== 显示函数 =====

def print_separator(char='=', width=56):
    print(char * width)


def display_question(q, index=None, total=None):
    """显示题目信息（不含答案）。"""
    type_name = TYPE_NAMES.get(q['type'], '未知')
    print_separator()
    if index is not None and total is not None:
        print(f" 第 {index}/{total} 题  [{type_name}]  错误率 {q.get('errorRate', '?')}%")
    else:
        print(f" [{type_name}]  错误率 {q.get('errorRate', '?')}%")
    print_separator('-')
    print(f" {q.get('question', '')}")
    if q.get('url'):
        print(f" [本题含图片]")
    for title, desc in zip(q.get('itemsTitleArray', []), q.get('itemsDescArray', [])):
        print(f"  {title}. {desc}")


def display_answer(q):
    """显示答案与解析。"""
    print_separator('-')
    print(f" 正确答案: {q.get('answer', '')}")
    skill = q.get('answerSkill', '')
    explain = q.get('answerSkillExplain', '')
    remark = strip_html(q.get('remark', ''))
    if skill:
        print(f" 答题技巧: {skill}")
    if explain:
        print(f" 解析: {explain}")
    if remark:
        print(f" 法律依据: {remark}")


def maybe_show_image(q):
    """如果题目含图片，自动显示。"""
    url = q.get('url', '')
    if not url:
        return True
    show_image(url)
    return True


# ===== 答题输入 =====

def get_user_answer(q):
    """获取用户答案，返回归一化字符串或 None（退出）。"""
    qtype = q['type']
    if qtype == TYPE_JUDGE:
        prompt = " 你的答案 (A=正确 B=错误, q=退出): "
    elif qtype == TYPE_MULTI:
        prompt = " 你的答案 (多选如 ABD 或 A,B,D, q=退出): "
    else:
        prompt = " 你的答案 (A/B/C/D, q=退出): "
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if raw.lower() in ('q', 'quit', 'exit'):
            return None
        ans = normalize_answer(raw)
        if not ans:
            print(" 输入无效，请重新输入。")
            continue
        # 按题型校验输入合法性
        if qtype == TYPE_JUDGE and len(ans) != 1:
            print(" 判断题只能输入一个答案 (A 或 B)。")
            continue
        if qtype == TYPE_SINGLE and len(ans) != 1:
            print(" 单选题只能输入一个字母。")
            continue
        if qtype == TYPE_MULTI and len(ans) < 2:
            print(" 多选题至少选择两个选项。")
            continue
        return ans


def check_answer(q, user_answer):
    """比对用户答案与正确答案。"""
    correct = normalize_answer(q.get('answer', ''))
    return user_answer == correct


# ===== 三种模式 =====

def practice_mode(questions, log, start_idx=0):
    """刷题模式：顺序、无限循环，用户先做题再看答案。
    答对自动下一题，答错才手动继续。"""
    total = len(questions)
    if total == 0:
        print(" 没有符合条件的题目。")
        return
    print(f"\n 刷题模式：共 {total} 道题，顺序循环，输入 q 可随时退出。\n")
    idx = start_idx
    session_correct = 0
    session_total = 0
    try:
        while True:
            q = questions[idx % total]
            print()
            display_question(q, index=idx % total + 1, total=total)
            print()
            if not maybe_show_image(q):
                break
            user = get_user_answer(q)
            if user is None:
                break
            session_total += 1
            qid = q['id']
            record_done(log, qid)
            correct = check_answer(q, user)
            if correct:
                session_correct += 1
                print()
                print(" >> 回答正确!")
                print()
                idx += 1
                continue
            print()
            print(f" >> 回答错误! 你的答案: {user}")
            record_wrong(log, qid)
            print()
            display_answer(q)
            print()
            print_separator()
            print(f" 本轮统计: {session_correct}/{session_total} 正确")
            print()
            try:
                cmd = input(" (回车=下一题 q=退出): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if cmd == 'q':
                break
            idx += 1
    finally:
        save_log(log)
    print(f"\n 本次刷题结束: 共做 {session_total} 题, 正确 {session_correct} 题。")


def memorize_mode(questions, log, start_idx=0):
    """背题模式：顺序、无限循环，直接展示答案与解析。"""
    total = len(questions)
    if total == 0:
        print(" 没有符合条件的题目。")
        return
    print(f"\n 背题模式：共 {total} 道题，顺序循环，输入 q 可随时退出。\n")
    idx = start_idx
    try:
        while True:
            q = questions[idx % total]
            print()
            display_question(q, index=idx % total + 1, total=total)
            print()
            if not maybe_show_image(q):
                break
            print()
            display_answer(q)
            record_done(log, q['id'])
            print()
            print_separator()
            print()
            try:
                cmd = input(" (回车=下一题 q=退出): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if cmd == 'q':
                break
            idx += 1
    finally:
        save_log(log)
    print("\n 背题结束。")


def mock_exam_mode(subject_questions, subject, log):
    """模拟考试模式：乱序出题，按真实考试规则计分。"""
    if not subject_questions:
        print(" 该科目无题目，无法考试。")
        return
    cfg = EXAM_CONFIG[subject]
    judges = [q for q in subject_questions if q['type'] == TYPE_JUDGE]
    singles = [q for q in subject_questions if q['type'] == TYPE_SINGLE]
    multis = [q for q in subject_questions if q['type'] == TYPE_MULTI]

    # 按配置抽取题目
    exam = []
    n_judge = min(cfg['judge'], len(judges))
    n_single = min(cfg['single'], len(singles))
    n_multi = min(cfg['multi'], len(multis))

    if n_judge < cfg['judge'] or n_single < cfg['single'] or n_multi < cfg['multi']:
        print(" 警告: 题库中某题型数量不足，将用可用题目组卷。")

    if n_judge:
        exam += random.sample(judges, n_judge)
    if n_single:
        exam += random.sample(singles, n_single)
    random.shuffle(exam)

    multi_part = []
    if n_multi:
        multi_part = random.sample(multis, n_multi)
        random.shuffle(multi_part)

    # 科四: 前40道判断+单选，最后10道多选；科一无多选
    exam = exam + multi_part

    total = len(exam)
    if total == 0:
        print(" 无法组卷，题目不足。")
        return
    full_score = total * cfg['per_score']
    # 题库不足时按 90% 比例调整合格线
    pass_score = round(full_score * 0.9) if total < cfg['count'] else cfg['pass_score']
    print(f"\n 模拟考试 - 科目{subject}")
    print_separator()
    print(f" 题数: {total} | 每题: {cfg['per_score']} 分 | 满分: {full_score} | 合格: {pass_score} 分")
    print(f" 考试中不显示答案，交卷后统一评分。输入 q 可放弃退出。")
    print_separator()

    wrong_list = []
    answered = 0
    try:
        for i, q in enumerate(exam, 1):
            print()
            display_question(q, index=i, total=total)
            print()
            if not maybe_show_image(q):
                print(" 已放弃考试。")
                return
            user = get_user_answer(q)
            if user is None:
                print(" 已放弃考试。")
                return
            answered += 1
            record_done(log, q['id'])
            if check_answer(q, user):
                print()
                print(" >> 回答正确!")
                print()
                continue
            print()
            print(f" >> 回答错误! 你的答案: {user} | 正确答案: {q.get('answer', '')}")
            record_wrong(log, q['id'])
            wrong_list.append((i, q, user))
            print()
            display_answer(q)
            print()
            try:
                cmd = input(" (回车=继续考试 q=放弃): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(" 已放弃考试。")
                return
            if cmd == 'q':
                print(" 已放弃考试。")
                return
        # 评分
        score = (answered - len(wrong_list)) * cfg['per_score']
        print()
        print_separator()
        print(f" 考试结束!")
        print(f" 得分: {score} / {full_score}")
        if score >= pass_score:
            print(f" 恭喜通过! (合格线 {pass_score} 分)")
        else:
            print(f" 未通过 (合格线 {pass_score} 分)")
        correct_n = answered - len(wrong_list)
        print(f" 答对 {correct_n} 题, 答错 {len(wrong_list)} 题")
        if wrong_list:
            print()
            print_separator()
            print(" === 错题回顾 ===")
            for qidx, q, user_ans in wrong_list:
                print_separator('-')
                print(f" 第{qidx}题: {q.get('question', '')}")
                print(f" 你的答案: {user_ans} | 正确答案: {q.get('answer', '')}")
                skill = q.get('answerSkill', '')
                explain = q.get('answerSkillExplain', '')
                if skill:
                    print(f" 答题技巧: {skill}")
                if explain:
                    print(f" 解析: {explain}")
                remark = strip_html(q.get('remark', ''))
                if remark:
                    print(f" 依据: {remark}")
    finally:
        save_log(log)
    print_separator()
    print(" 考试结束，返回主菜单。")


# ===== 题目筛选 =====

def filter_questions(questions, log, filter_type):
    """根据筛选条件过滤题目。"""
    if filter_type == 1:
        return list(questions)
    elif filter_type == 2:
        return [q for q in questions if str(q['id']) not in log['done']]
    elif filter_type == 3:
        return [q for q in questions if str(q['id']) in log['wrong']]
    return list(questions)


# ===== 菜单交互 =====

def select_subject():
    """选择科目。"""
    print()
    print_separator()
    print(" 请选择科目:")
    print("   1 = 科目一")
    print("   4 = 科目四")
    print("   r = 重置答题进度")
    print("   q = 退出")
    print()
    while True:
        try:
            choice = input(" 选择: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice == 'q':
            return None
        if choice in ('1', '4'):
            return int(choice)
        if choice == 'r':
            return 'reset'
        print(" 输入无效。")


def select_mode():
    """选择刷题模式。"""
    print()
    print_separator()
    print(" 请选择模式:")
    print("   1 = 刷题 ")
    print("   2 = 背题 ")
    print("   3 = 模拟考试")
    print("   q = 返回")
    print()
    while True:
        try:
            choice = input(" 选择: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice == 'q':
            return None
        if choice in ('1', '2', '3'):
            return int(choice)
        print(" 输入无效。")


def select_filter(subject_total):
    """选择题目范围，返回 (filter_type, start_idx) 或 None。"""
    print()
    print_separator()
    print(" 请选择题目范围:")
    print("   1 = 全部题")
    print("   2 = 只刷没做过的题")
    print("   3 = 只刷错题")
    print(f"   4 = 跳转到指定题号 (1~{subject_total})")
    print("   q = 返回")
    print()
    while True:
        try:
            choice = input(" 选择: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice == 'q':
            return None
        if choice in ('1', '2', '3'):
            return (int(choice), 0)
        if choice == '4':
            print()
            try:
                num_str = input(f" 跳转到第几题 (1~{subject_total}): ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            try:
                num = int(num_str)
            except ValueError:
                print(" 输入无效。")
                continue
            if num < 1 or num > subject_total:
                print(f" 题号超出范围 (1~{subject_total})。")
                continue
            return (1, num - 1)
        print(" 输入无效。")


def show_stats(log):
    """显示刷题进度统计。"""
    done_count = len(log.get('done', {}))
    wrong_count = len(log.get('wrong', {}))
    print()
    print_separator()
    print(f" 刷题进度: 已做 {done_count} 题, 错题本 {wrong_count} 题")
    print()


def reset_progress(log):
    """重置答题进度（清空已做和错题记录）。"""
    print()
    print_separator()
    print(" 确认重置答题进度?")
    print(" 此操作将清空所有已做记录和错题本, 且不可恢复!")
    print()
    try:
        confirm = input(" 输入 y 确认重置, 其它键取消: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(" 已取消。")
        return log
    if confirm != 'y':
        print(" 已取消。")
        return log
    log = {"done": {}, "wrong": {}}
    save_log(log)
    print()
    print(" 进度已重置。")
    print()
    return log


# ===== 主入口 =====

def main():
    print()
    print_separator()
    print("        驾考题库刷题工具")
    print_separator()
    print()

    if not BANK_PATH.exists():
        print(f" 错误: 题库文件不存在: {BANK_PATH}")
        try:
            input(" 按回车退出...")
        except (EOFError, KeyboardInterrupt):
            pass
        return

    print(" 正在加载题库...")
    try:
        bank = load_bank()
    except Exception as e:
        print(f" 加载题库失败: {e}")
        try:
            input(" 按回车退出...")
        except (EOFError, KeyboardInterrupt):
            pass
        return
    print(f" 已加载 {len(bank)} 道题")
    print()

    log = load_log()
    show_stats(log)

    while True:
        subject = select_subject()
        if subject is None:
            break

        if subject == 'reset':
            log = reset_progress(log)
            show_stats(log)
            continue

        subject_questions = [q for q in bank if q.get('subject') == subject]
        print()
        print(f" 科目{subject} 共 {len(subject_questions)} 道题")
        print()

        mode = select_mode()
        if mode is None:
            continue

        if mode in (1, 2):
            result = select_filter(len(subject_questions))
            if result is None:
                continue
            filter_type, start_idx = result
            questions = filter_questions(subject_questions, log, filter_type)
            if not questions:
                print()
                print(" 没有符合条件的题目，请更换筛选条件。")
                print()
                continue
            print()
            if start_idx > 0:
                print(f" 将从第 {start_idx + 1} 题开始")
                print()
            print(f" 本次共 {len(questions)} 道题")
            print()
            if mode == 1:
                practice_mode(questions, log, start_idx)
            else:
                memorize_mode(questions, log, start_idx)
            show_stats(log)
        elif mode == 3:
            mock_exam_mode(subject_questions, subject, log)
            show_stats(log)

        print()
        print(" 返回主菜单...")
        print()

    save_log(log)
    print()
    print(" 已保存日志，再见!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n 已中断。")
