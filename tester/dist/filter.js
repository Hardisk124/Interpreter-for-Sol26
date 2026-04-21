/**
 * @file filter.ts
 * @brief This model is responsible for filtering tests based on CLI parameters. Fileter based on 2 criteria:
 * - Include/Exclude lists of categories and test names
 * - Tests which cannot go trhough filter goes to unececuted with code FILTERED_OUT but stays in discovered test cases, so they are visible in the final report.
 * @author Martin Turčan <xturcam@vutbr.cz>
 */
import { UnexecutedReason, UnexecutedReasonCode } from "./models.js";
/**
 * @brief Check if a value matches any of the given patterns
 * @param value The string to check
 * @param patterns The list of patterns to match against
 * @param useRegex Whether to use regex matching
 * @returns True if the value matches any pattern, false otherwise
 */
function matches(value, patterns, useRegex) {
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
function isIncluded(test, args) {
    const { include, include_category, include_test, regex_filters } = args;
    //no include filters means include all
    if (include === null && include_category === null && include_test === null)
        return true;
    //-i compares both category and name, -ic compares only category, -it compares only name
    if (include !== null && matches(test.name, include, regex_filters))
        return true;
    if (include !== null && matches(test.category, include, regex_filters))
        return true;
    if (include_category !== null && matches(test.category, include_category, regex_filters))
        return true;
    if (include_test !== null && matches(test.name, include_test, regex_filters))
        return true;
    return false;
}
/**
 * @brief Determines whether a test case should be excluded
 * @param test The test case definition to check
 * @param args The filter arguments from CLI
 * @returns true if the test should be excluded, false otherwise
 */
function isExcluded(test, args) {
    const { exclude, exclude_category, exclude_test, regex_filters } = args;
    //-e compares both category and name, -ec compares only category, -et compares only name
    if (exclude !== null && matches(test.name, exclude, regex_filters))
        return true;
    if (exclude !== null && matches(test.category, exclude, regex_filters))
        return true;
    if (exclude_category !== null && matches(test.category, exclude_category, regex_filters))
        return true;
    if (exclude_test !== null && matches(test.name, exclude_test, regex_filters))
        return true;
    return false;
}
/**
 * @brief Applies the include/exclude filters to the list of discovered tests
 * @param tests The list of discovered test cases to filter
 * @param args The filter arguments from CLI
 * @returns FilterResult with the list of tests
 */
export function filterTests(tests, args) {
    const toRun = [];
    const filtered = {};
    for (const test of tests) {
        if (isIncluded(test, args) && !isExcluded(test, args)) {
            toRun.push(test);
        }
        else {
            filtered[test.name] = new UnexecutedReason(UnexecutedReasonCode.FILTERED_OUT, "Test case was filtered out based on the provided include/exclude criteria.");
        }
    }
    return { toRun, filtered };
}
//# sourceMappingURL=filter.js.map