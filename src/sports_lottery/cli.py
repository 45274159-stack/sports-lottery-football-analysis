from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .analysis import estimate_match
from .database import connect, import_rows
from .review import render_review
from .schema import validate_csv
from .sporttery_source import SourceBlocked, collect_results, save_snapshot
from .prematch_source import collect_prematch, save_prematch_snapshot


def _validate(path: str) -> int:
    rows, issues = validate_csv(path)
    if issues:
        for issue in issues:
            print(f"第{issue.row}行 [{issue.field}] {issue.message}")
        return 1
    print(f"校验通过：{len(rows)} 场")
    return 0


def _import(path: str, database: str) -> int:
    rows, issues = validate_csv(path)
    if issues:
        for issue in issues:
            print(f"第{issue.row}行 [{issue.field}] {issue.message}")
        return 1
    connection = connect(database)
    changes = import_rows(connection, rows)
    print(f"导入完成：{len(rows)} 场，数据库变更 {changes} 行")
    return 0


def _analyze(database: str, home: str, away: str, kickoff: str) -> int:
    estimate = estimate_match(connect(database), home, away, kickoff)
    print(f"预期进球：{home} {estimate.expected_home_goals:.2f} - {estimate.expected_away_goals:.2f} {away}")
    print(f"胜平负：主胜 {estimate.home_win:.1%} / 平 {estimate.draw:.1%} / 客胜 {estimate.away_win:.1%}")
    print("参考比分：" + "，".join(f"{score} {probability:.1%}" for score, probability in estimate.top_scores))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="竞彩足球历史数据工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="校验标准CSV")
    validate.add_argument("csv")

    initialize = subparsers.add_parser("init-db", help="初始化SQLite数据库")
    initialize.add_argument("--db", default="data/processed/sporttery.sqlite3")

    importer = subparsers.add_parser("import", help="校验并导入CSV")
    importer.add_argument("csv")
    importer.add_argument("--db", default="data/processed/sporttery.sqlite3")

    analyze = subparsers.add_parser("analyze", help="生成透明的赛前基线预测")
    analyze.add_argument("--db", default="data/processed/sporttery.sqlite3")
    analyze.add_argument("--home", required=True)
    analyze.add_argument("--away", required=True)
    analyze.add_argument("--kickoff", required=True)

    review = subparsers.add_parser("review-history", help="复盘标准化历史赛果")
    review.add_argument("directory", nargs="?", default="data/processed/top5_2016_2026")

    collect = subparsers.add_parser("collect-sporttery", help="从体彩官方公开接口逐日采集赛果")
    collect.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    collect.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    collect.add_argument("--output", required=True, help="原始JSON快照输出路径")
    collect.add_argument("--delay", type=float, default=0.4, help="分页请求间隔秒数")

    prematch = subparsers.add_parser("collect-prematch", help="采集固定奖金、伤停与新赛季技术资料")
    prematch.add_argument("--date", required=True, help="受注日期 YYYY-MM-DD")
    prematch.add_argument("--output", required=True, help="不可变JSON快照输出路径")
    prematch.add_argument("--delay", type=float, default=0.25, help="明细请求间隔秒数")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate":
        return _validate(args.csv)
    if args.command == "init-db":
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        connect(args.db).close()
        print(f"数据库已初始化：{args.db}")
        return 0
    if args.command == "import":
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        return _import(args.csv, args.db)
    if args.command == "review-history":
        print(render_review(args.directory))
        return 0
    if args.command == "collect-sporttery":
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
        if start > end:
            raise SystemExit("开始日期不能晚于结束日期")
        try:
            rows = collect_results(start, end, delay=max(0.0, args.delay))
        except SourceBlocked as error:
            print(f"采集停止：{error}")
            print("请使用官方允许的数据导出或授权服务；不要绕过网站安全策略。")
            return 2
        save_snapshot(args.output, rows, start, end)
        print(f"采集完成：{len(rows)} 场，保存至 {args.output}")
        return 0
    if args.command == "collect-prematch":
        try:
            payload = collect_prematch(date.fromisoformat(args.date), delay=max(0.0, args.delay))
        except SourceBlocked as error:
            print(f"采集停止：{error}")
            print("请使用官方允许的数据导出或授权服务；不要绕过网站安全策略。")
            return 2
        save_prematch_snapshot(args.output, payload)
        print(f"采集完成：{payload['fixture_count']} 场，保存至 {args.output}")
        return 0
    return _analyze(args.db, args.home, args.away, args.kickoff)


if __name__ == "__main__":
    raise SystemExit(main())
