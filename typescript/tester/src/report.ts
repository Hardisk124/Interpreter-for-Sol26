/**
 * @file report.ts
 * @brief This module is responsible for generating the final report in JSON format based on the test results.
 * Reports are formatted by category containing:
 * -total_points: total points for the category
 * -passed_points: points obtained only from passed tests
 * -test_results: map name -> TestCaseResult
 * in --dry-run -> result null
 * @author Martin Turčan <xturcam00@vutbr.cz>
 */

import {
  TestCaseDefinition,
  TestCaseReport,
  TestResult,
  CategoryReport,
  TestReport,
  UnexecutedReason,
} from "./models.js";

export function generateReport(
  discovered: TestCaseDefinition[],
  unexecuted: Record<string, UnexecutedReason>,
  results: Map<string, { test: TestCaseDefinition; report: TestCaseReport }>,
  dryRun: boolean
): TestReport {
  if (dryRun) {
    return new TestReport({ discovered_test_cases: discovered, unexecuted, results: null });
  }

  // Group results by category
  const byCategory = new Map<string, { test: TestCaseDefinition; report: TestCaseReport }[]>();
  for (const entry of results.values()) {
    const category = entry.test.category;
    let categoryEntries = byCategory.get(category);
    if (categoryEntries === undefined) {
      categoryEntries = [];
      byCategory.set(category, categoryEntries);
    }
    categoryEntries.push(entry);
  }
  // Create category reports and calculate points
  const categoryReports: Record<string, CategoryReport> = {};
  for (const [category, entries] of byCategory) {
    let totalPoints = 0;
    let passedPoints = 0;
    const testResults: Record<string, TestCaseReport> = {};

    for (const { test, report } of entries) {
      totalPoints += test.points;
      if (report.result === TestResult.PASSED) {
        passedPoints += test.points;
      }
      testResults[test.name] = report;
    }
    categoryReports[category] = new CategoryReport(totalPoints, passedPoints, testResults);
  }

  return new TestReport({
    discovered_test_cases: discovered,
    unexecuted,
    results: categoryReports,
  });
}
