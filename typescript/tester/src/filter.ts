/**
 * @file filter.ts
 * @brief This model is responsible for filtering tests based on CLI parameters. Fileter based on 2 criteria:
 * - Include/Exclude lists of categories and test names
 * - Tests which cannot go trhough filter goes to unececuted with code FILTERED_OUT but stays in discovered test cases, so they are visible in the final report.
 * @author Martin Turčan <xturcam@vutbr.cz>
 */

import { TestCaseDefinition, UnexecutedReason, UnexecutedReasonCode } from "./models.js";

// subset of CLI arguments related to filtering
interface FilterArgs {
  include: string[] | null;
  include_category: string[] | null;
  include_test: string[] | null;
  exclude: string[] | null;
  exclude_category: string[] | null;
  exclude_test: string[] | null;
  regex_filters: boolean;
}

/**
 * @brief Check if a value matches any of the given patterns
 * @param value The string to check
 * @param patterns The list of patterns to match against
 * @param useRegex Whether to use regex matching
 * @returns True if the value matches any pattern, false otherwise
 */
function matches(value: string, patterns: string[], useRegex: boolean): boolean {
  if (useRegex) {
    return patterns.some((p) => new RegExp(p).test(value));
  }
  return patterns.some((p) => p.trim() === value);
}

/**
 * @brief Determines whether a test case should be included
 * @param test The test case definition to check
 * @param args The filter arguments from CLI
 * @return true if the test should be included, false otherwise
 */
function isIncluded(test: TestCaseDefinition, args: FilterArgs): boolean {
  const { include, include_category, include_test, regex_filters } = args;

  //no include filters means include all
  if (include === null && include_category === null && include_test === null) return true;

  //-i compares both category and name, -ic compares only category, -it compares only name
  if (include !== null && matches(test.name, include, regex_filters)) return true;
  if (include !== null && matches(test.category, include, regex_filters)) return true;

  if (include_category !== null && matches(test.category, include_category, regex_filters))
    return true;

  if (include_test !== null && matches(test.name, include_test, regex_filters)) return true;

  return false;
}

/**
 * @brief Determines whether a test case should be excluded
 * @param test The test case definition to check
 * @param args The filter arguments from CLI
 * @returns true if the test should be excluded, false otherwise
 */
function isExcluded(test: TestCaseDefinition, args: FilterArgs): boolean {
  const { exclude, exclude_category, exclude_test, regex_filters } = args;

  //-e compares both category and name, -ec compares only category, -et compares only name
  if (exclude !== null && matches(test.name, exclude, regex_filters)) return true;
  if (exclude !== null && matches(test.category, exclude, regex_filters)) return true;

  if (exclude_category !== null && matches(test.category, exclude_category, regex_filters))
    return true;

  if (exclude_test !== null && matches(test.name, exclude_test, regex_filters)) return true;

  return false;
}

export interface FilterResult {
  //tests that passed the filter and should be executed
  toRun: TestCaseDefinition[];
  //tests that were filtered out, key is test name
  filtered: Record<string, UnexecutedReason>;
}

/**
 * @brief Applies the include/exclude filters to the list of discovered tests
 * @param tests The list of discovered test cases to filter
 * @param args The filter arguments from CLI
 * @returns FilterResult with the list of tests
 */
export function filterTests(tests: TestCaseDefinition[], args: FilterArgs): FilterResult {
  const toRun: TestCaseDefinition[] = [];
  const filtered: Record<string, UnexecutedReason> = {};

  for (const test of tests) {
    if (isIncluded(test, args) && !isExcluded(test, args)) {
      toRun.push(test);
    } else {
      filtered[test.name] = new UnexecutedReason(
        UnexecutedReasonCode.FILTERED_OUT,
        "Test case was filtered out based on the provided include/exclude criteria."
      );
    }
  }
  return { toRun, filtered };
}
