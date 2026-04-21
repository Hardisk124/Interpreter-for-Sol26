/**
 * This module defines the data models used for representing test cases and their results.
 * It serves as the reference for the testing tool's expected output data structure.
 *
 * Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
 *
 * AI usage notice: The author used OpenAI Codex to create the implementation of this
 *                  module based on its Python counterpart.
 */
// ---- Test cases ----
export var TestCaseType;
(function (TestCaseType) {
    /** Represents the type of a test case: SOL2XML, interpretation only, combined. */
    TestCaseType[TestCaseType["PARSE_ONLY"] = 0] = "PARSE_ONLY";
    TestCaseType[TestCaseType["EXECUTE_ONLY"] = 1] = "EXECUTE_ONLY";
    TestCaseType[TestCaseType["COMBINED"] = 2] = "COMBINED";
})(TestCaseType || (TestCaseType = {}));
export class TestCaseDefinitionFile {
    /**
     * Represents a single discovered test case file.
     *
     * IPP: This model may (or may not) be useful for your internal processing, or you may
     *      choose to create your own internal models and only in the end create the final
     *      TestCaseDefinition instances to include in the output report.
     *
     *      Do not modify this model directly, as it is used as the parent of the
     *      TestCaseDefinition model, which is included in the output report.
     */
    /** The test case name, derived from the test case file name without the '.test' extension. */
    name;
    /** Path to the test case definition file ('.test'). */
    test_source_path;
    /**
     * Path to a file with the standard input contents for the interpreter.
     * Present if the '.in' file was discovered.
     */
    stdin_file;
    /**
     * Path to a file with the expected standard output of the interpreter.
     * Present if the '.out' file was discovered.
     */
    expected_stdout_file;
    constructor(init) {
        this.name = init.name;
        this.test_source_path = init.test_source_path;
        this.stdin_file = init.stdin_file ?? null;
        this.expected_stdout_file = init.expected_stdout_file ?? null;
    }
}
export class TestCaseDefinition extends TestCaseDefinitionFile {
    /**
     * Represents a single discovered test case (that was successfully parsed).
     *
     * IPP: Do not modify this model directly, as it is also used in the output report.
     *      You may create your own internal models derived from this one.
     */
    /**
     * The type of the test case, which determines how it should be executed
     * and what exit codes are expected.
     */
    test_type;
    /** An optional human-readable description of the test case. */
    description;
    /**
     * A string identifier of a category to which this test case belongs.
     * Used for grouping test cases in the final report and for filtering which test cases to execute.
     */
    category;
    /** The number of points awarded for passing this test case. */
    points;
    /**
     * A list of expected parser exit codes.
     * Must be present for parser-only test cases.
     * Must be null for interpreter-only test cases.
     * Must be null or [0] for combined test cases.
     */
    expected_parser_exit_codes;
    /**
     * A list of expected interpreter exit code.
     * Must be present for interpreter-only and combined test cases.
     * Must be null for parser-only test cases.
     */
    expected_interpreter_exit_codes;
    constructor(init) {
        super(init);
        this.test_type = init.test_type;
        this.description = init.description ?? null;
        this.category = init.category;
        this.points = init.points ?? 1;
        this.expected_parser_exit_codes = init.expected_parser_exit_codes ?? null;
        this.expected_interpreter_exit_codes = init.expected_interpreter_exit_codes ?? null;
        this.validateExitCodes();
    }
    static hasNoExitCodes(exitCodes) {
        return exitCodes === null || exitCodes.length === 0;
    }
    validateParseOnlyExitCodes() {
        if (TestCaseDefinition.hasNoExitCodes(this.expected_parser_exit_codes)) {
            throw new Error("Expected parser exit codes must be provided for parse-only test cases.");
        }
        if (this.expected_interpreter_exit_codes !== null) {
            throw new Error("Expected interpreter exit codes should not be provided for parse-only test cases.");
        }
    }
    validateExecuteOnlyExitCodes() {
        if (TestCaseDefinition.hasNoExitCodes(this.expected_interpreter_exit_codes)) {
            throw new Error("Expected interpreter exit codes must be provided for execute-only test cases.");
        }
        if (this.expected_parser_exit_codes !== null) {
            throw new Error("Expected parser exit codes should not be provided for execute-only test cases.");
        }
    }
    validateCombinedExitCodes() {
        if (this.expected_parser_exit_codes !== null &&
            (this.expected_parser_exit_codes.length !== 1 || this.expected_parser_exit_codes[0] !== 0)) {
            throw new Error("In combined test cases, the parser exit code must be zero.");
        }
        if (TestCaseDefinition.hasNoExitCodes(this.expected_interpreter_exit_codes)) {
            throw new Error("Expected interpreter exit codes must be provided for combined test cases.");
        }
    }
    validateExitCodes() {
        /**
         * Validates that the expected exit codes are provided correctly based on the test case type.
         */
        switch (this.test_type) {
            case TestCaseType.PARSE_ONLY:
                this.validateParseOnlyExitCodes();
                return;
            case TestCaseType.EXECUTE_ONLY:
                this.validateExecuteOnlyExitCodes();
                return;
            case TestCaseType.COMBINED:
                this.validateCombinedExitCodes();
                return;
        }
    }
}
// ---- Output ----
export var UnexecutedReasonCode;
(function (UnexecutedReasonCode) {
    /** The test case was filtered out based on the provided include/exclude criteria. */
    UnexecutedReasonCode[UnexecutedReasonCode["FILTERED_OUT"] = 0] = "FILTERED_OUT";
    /** The test case file could not be parsed as a valid SOLtest. */
    UnexecutedReasonCode[UnexecutedReasonCode["MALFORMED_TEST_CASE_FILE"] = 1] = "MALFORMED_TEST_CASE_FILE";
    /** The type of the test case could not be (unambiguously) determined from the provided specification. */
    UnexecutedReasonCode[UnexecutedReasonCode["CANNOT_DETERMINE_TYPE"] = 2] = "CANNOT_DETERMINE_TYPE";
    /** It was not possible to run the external executable that was required for the test. */
    UnexecutedReasonCode[UnexecutedReasonCode["CANNOT_EXECUTE"] = 3] = "CANNOT_EXECUTE";
    /** Unexpected error. */
    UnexecutedReasonCode[UnexecutedReasonCode["OTHER"] = 4] = "OTHER";
})(UnexecutedReasonCode || (UnexecutedReasonCode = {}));
export class UnexecutedReason {
    code;
    message;
    /**
     * Represents the reason why a test case was not executed, including an optional
     * human-readable message.
     *
     * IPP: Choose a suitable message, it won't be evaluated automatically.
     */
    constructor(code, message = null) {
        this.code = code;
        this.message = message;
    }
}
export var TestResult;
(function (TestResult) {
    /** Represents the result of an executed test case. */
    TestResult["PASSED"] = "passed";
    TestResult["UNEXPECTED_PARSER_EXIT_CODE"] = "parse_fail";
    TestResult["UNEXPECTED_INTERPRETER_EXIT_CODE"] = "int_fail";
    TestResult["INTERPRETER_RESULT_DIFFERS"] = "diff_fail";
})(TestResult || (TestResult = {}));
export class TestCaseReport {
    result;
    parser_exit_code;
    interpreter_exit_code;
    parser_stdout;
    parser_stderr;
    interpreter_stdout;
    interpreter_stderr;
    diff_output;
    /** Represents the report for a single test case after processing. */
    constructor(result, parser_exit_code = null, interpreter_exit_code = null, parser_stdout = null, parser_stderr = null, interpreter_stdout = null, interpreter_stderr = null, diff_output = null) {
        this.result = result;
        this.parser_exit_code = parser_exit_code;
        this.interpreter_exit_code = interpreter_exit_code;
        this.parser_stdout = parser_stdout;
        this.parser_stderr = parser_stderr;
        this.interpreter_stdout = interpreter_stdout;
        this.interpreter_stderr = interpreter_stderr;
        this.diff_output = diff_output;
    }
}
export class CategoryReport {
    total_points;
    passed_points;
    test_results;
    /** Represents the report for a category of test cases. */
    constructor(
    /** The sum of points for all executed test cases in this category. */
    total_points, 
    /** The sum of points for all passed test cases in this category. */
    passed_points, 
    /** A mapping from test case names to their individual reports. */
    test_results) {
        this.total_points = total_points;
        this.passed_points = passed_points;
        this.test_results = test_results;
    }
}
export class TestReport {
    /** Represents the report generated after processing the test cases. */
    /** A list of all discovered test cases that were successfully parsed. */
    discovered_test_cases;
    /** A mapping from a test case name to the reason why it was not executed. */
    unexecuted;
    results;
    constructor(init) {
        this.discovered_test_cases = init.discovered_test_cases ?? [];
        this.unexecuted = init.unexecuted ?? {};
        this.results = init.results ?? null;
    }
    toJSON() {
        const result = {
            discovered_test_cases: this.discovered_test_cases,
            unexecuted: this.unexecuted,
        };
        // The 'results' field is only included in the report if at least one test case was executed.
        if (this.results !== null && Object.keys(this.results).length > 0) {
            result["results"] = this.results;
        }
        return result;
    }
}
//# sourceMappingURL=models.js.map