from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import estimate_match
from .database import connect, import_rows
from .review import render_review
from .schema import validate_csv


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
    return _analyze(args.db, args.home, args.away, args.kickoff)


if __name__ == "__main__":
    raise SystemExit(main())
