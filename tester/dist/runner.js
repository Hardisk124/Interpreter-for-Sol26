/**
 * @file runner.ts
 * @brief This module is responsible for executing the discovered test cases and generating the final report.
 * It should execute the tests based on their type (parse-only, execute-only, combined) and collect the results.
 * The results should include the actual exit codes and outputs,
 * which will be compared against the expected values in the final report.
 * @author Martin Turčan <xturcam00@vutbr.cz>
 */
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { TestCaseType, TestCaseReport, TestResult, UnexecutedReason, UnexecutedReasonCode, } from "./models.js";
/**
 * @brief loads path to sol2xml and interpreter from environment variables, or uses default values if not set.
 * @returns RunnerConfig object with paths to parser and interpreter
 */
export function loadConfig() {
    const parserPath = process.env["SOL2XML_PATH"] ?? "sol2xml";
    const interpreterPath = process.env["INTERPRETER_PATH"] ?? "interpreter";
    return { parserPath, interpreterPath };
}
/**
 * @brief Run extern process synchronously
 * @param bin path to executable file
 * @param args arguments of command line
 * @param stdinFile path to file with stdin content, if null, no stdin is provided
 * @return ExecResult object with exit code, stdout, stderr and failed flag (true if process failed to start or was killed)
 */
function execPrecess(bin, args, stdinFile) {
    const opts = {
        encoding: "utf-8",
        maxBuffer: 10 * 1024 * 1024, // 10 MB
    };
    if (stdinFile !== null) {
        opts.input = readFileSync(stdinFile, "utf-8");
    }
    const result = spawnSync(bin, args, opts);
    if (result.error !== undefined) {
        return {
            exitCode: -1,
            stdout: "",
            stderr: result.error.message,
            failed: true,
        };
    }
    const stdout = typeof result.stdout === "string" ? result.stdout : "";
    const stderr = typeof result.stderr === "string" ? result.stderr : "";
    return {
        exitCode: result.status ?? -1,
        stdout,
        stderr,
        failed: false,
    };
}
/**
 * @brief Run the parser on the given source file
 * @param parserPath path to the parser executable
 * @param sourcePath path to the source file to be parsed
 * @return ExecResult object with exit code, stdout, stderr and failed flag
 */
function runParser(parserPath, sourcePath) {
    return execPrecess(parserPath, [sourcePath], null);
}
/**
 * @brief Extract SOL26 program source code from a SOLtest file by removing its header section.
 * @param testFilePath path to the .test file
 * @returns source code content after the first empty line
 */
function extractSourceCode(testFilePath) {
    const content = readFileSync(testFilePath, "utf-8");
    const lines = content.split(/\r?\n/);
    let i = 0;
    while (i < lines.length) {
        if ((lines[i] ?? "").trim() === "") {
            i++;
            break;
        }
        i++;
    }
    return lines.slice(i).join("\n");
}
/**
 * @brief Writes extracted source code to a temporary file for parser execution.
 * @param content source code to write
 * @returns object with path to temporary file and cleanup function
 */
function writeTempSource(content) {
    const tmpDir = mkdtempSync(join(tmpdir(), "sol26-src-"));
    const path = join(tmpDir, "source.sol");
    writeFileSync(path, content, "utf-8");
    return {
        path,
        cleanup: () => {
            try {
                rmSync(tmpDir, { recursive: true });
            }
            catch {
                // Ignore errors during cleanup
            }
        },
    };
}
/**
 * @brief Run the interpreter on the given XML file
 * @param interpreterPath path to the interpreter executable
 * @param xmlFile path to the XML file to be interpreted
 * @param stdinFile path to the file with stdin content, if null, no stdin is provided
 * @return ExecResult object with exit code, stdout, stderr and failed flag
 */
function runInterpreter(interpreterPath, xmlFile, stdinFile) {
    const args = ["-s", xmlFile];
    if (stdinFile !== null) {
        args.push("-i", stdinFile);
    }
    return execPrecess(interpreterPath, args, null);
}
/**
 * @brief Writes content to a temporary file
 * @param content string content to be written to the temporary file
 * @return object with path to the temporary file and cleanup function to delete the file after
 */
function writeTempXml(content) {
    const tmpDir = mkdtempSync(join(tmpdir(), "sol26-"));
    const path = join(tmpDir, "output.xml");
    writeFileSync(path, content, "utf-8");
    return {
        path,
        cleanup: () => {
            try {
                rmSync(tmpDir, { recursive: true });
            }
            catch {
                // Ignore errors during cleanup
            }
        },
    };
}
/**
 * @brief Runs the diff command to compare expected and actual output files
 * @param expected path to the file with expected output
 * @param actual string with actual output to be compared
 * @return string with diff output if there are differences, or null if there are no differences
 */
function runDiff(expected, actual) {
    const tmpDir = mkdtempSync(join(tmpdir(), "sol26-diff-"));
    const actualFile = join(tmpDir, "actual.out");
    try {
        writeFileSync(actualFile, actual, "utf-8");
        const diffResult = spawnSync("diff", [expected, actualFile], { encoding: "utf-8" });
        // exit code 0 means no differences
        if (diffResult.status === 0) {
            return null; // No differences
        }
        return diffResult.stdout;
    }
    finally {
        //delete temporary directory and files after diffing
        try {
            rmSync(tmpDir, { recursive: true });
        }
        catch {
            /* ignore errors */
        }
    }
}
/**
 * @brief Runs a test case based on its type
 * @param testCase definition of the test case to be run
 * @param config configuration with paths to parser and interpreter
 * @return RunResult object with the report of the test case
 */
export function runTest(testCase, config) {
    switch (testCase.test_type) {
        case TestCaseType.PARSE_ONLY:
            return runParseOnly(testCase, config);
        case TestCaseType.EXECUTE_ONLY:
            return runExecuteOnly(testCase, config);
        case TestCaseType.COMBINED:
            return runCombined(testCase, config);
    }
}
/**
 * @brief Runs a test case that only involves parsing
 * @param testCase definition of the test case to be run
 * @param config configuration with paths to parser and interpreter
 * @return RunResult object with the report of the test case
 */
function runParseOnly(testCase, config) {
    let parser;
    try {
        const sourceCode = extractSourceCode(testCase.test_source_path);
        const tempSource = writeTempSource(sourceCode);
        try {
            parser = runParser(config.parserPath, tempSource.path);
        }
        finally {
            tempSource.cleanup();
        }
    }
    catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
            kind: "unexecuted",
            reason: new UnexecutedReason(UnexecutedReasonCode.OTHER, `Failed to prepare parser input: ${message}`),
        };
    }
    if (parser.failed) {
        return {
            kind: "unexecuted",
            reason: new UnexecutedReason(UnexecutedReasonCode.CANNOT_EXECUTE, `Failed to execute parser: ${parser.stderr}`),
        };
    }
    const passed = (testCase.expected_parser_exit_codes ?? []).includes(parser.exitCode);
    return {
        kind: "report",
        report: new TestCaseReport(passed ? TestResult.PASSED : TestResult.UNEXPECTED_PARSER_EXIT_CODE, parser.exitCode, null, parser.stdout, parser.stderr, null, null, null),
    };
}
/**
 * @brief Runs a test case that only involves execution
 * @param testCase definition of the test case to be run
 * @param config configuration with paths to parser and interpreter
 * @return RunResult object with the report of the test case
 */
function runExecuteOnly(testCase, config) {
    let interpreter;
    try {
        const sourceCode = extractSourceCode(testCase.test_source_path);
        const tempSource = writeTempSource(sourceCode);
        try {
            interpreter = runInterpreter(config.interpreterPath, tempSource.path, testCase.stdin_file);
        }
        finally {
            tempSource.cleanup();
        }
    }
    catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
            kind: "unexecuted",
            reason: new UnexecutedReason(UnexecutedReasonCode.OTHER, `Failed to prepare interpreter input: ${message}`),
        };
    }
    if (interpreter.failed) {
        return {
            kind: "unexecuted",
            reason: new UnexecutedReason(UnexecutedReasonCode.CANNOT_EXECUTE, `Failed to execute interpreter: ${interpreter.stderr}`),
        };
    }
    return buildInterpreterReport(testCase, null, null, null, interpreter);
}
/**
 * @brief Runs a test case that involves both parsing and execution
 * @param testCase definition of the test case to be run
 * @param config configuration with paths to parser and interpreter
 * @return RunResult object with the report of the test case
 */
function runCombined(testCase, config) {
    let parser;
    try {
        const sourceCode = extractSourceCode(testCase.test_source_path);
        const tempSource = writeTempSource(sourceCode);
        try {
            parser = runParser(config.parserPath, tempSource.path);
        }
        finally {
            tempSource.cleanup();
        }
    }
    catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
            kind: "unexecuted",
            reason: new UnexecutedReason(UnexecutedReasonCode.OTHER, `Failed to prepare parser input: ${message}`),
        };
    }
    //parse sol26 to xml, if parser fails to execute, we cannot run the test
    if (parser.failed) {
        return {
            kind: "unexecuted",
            reason: new UnexecutedReason(UnexecutedReasonCode.CANNOT_EXECUTE, `Failed to execute parser: ${parser.stderr}`),
        };
    }
    if (parser.exitCode !== 0) {
        return {
            kind: "report",
            report: new TestCaseReport(TestResult.UNEXPECTED_PARSER_EXIT_CODE, parser.exitCode, null, parser.stdout, parser.stderr, null, null, null),
        };
    }
    //write parser output to temporary file and give to interpreter
    const tempXml = writeTempXml(parser.stdout);
    try {
        const interpreter = runInterpreter(config.interpreterPath, tempXml.path, testCase.stdin_file);
        if (interpreter.failed) {
            return {
                kind: "unexecuted",
                reason: new UnexecutedReason(UnexecutedReasonCode.CANNOT_EXECUTE, `Failed to execute interpreter: ${interpreter.stderr}`),
            };
        }
        return buildInterpreterReport(testCase, parser.exitCode, parser.stdout, parser.stderr, interpreter);
    }
    finally {
        tempXml.cleanup();
    }
}
function buildInterpreterReport(testCase, parserExitCode, parserStdout, parserStderr, interpreter) {
    const exitOk = (testCase.expected_interpreter_exit_codes ?? []).includes(interpreter.exitCode);
    if (!exitOk) {
        return {
            kind: "report",
            report: new TestCaseReport(TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE, parserExitCode, interpreter.exitCode, parserStdout, parserStderr, interpreter.stdout, interpreter.stderr, null),
        };
    }
    //diff only if .out exists and interpreter exit code is ok
    let diffOutput = null;
    let result = TestResult.PASSED;
    if (testCase.expected_stdout_file !== null && interpreter.exitCode === 0) {
        diffOutput = runDiff(testCase.expected_stdout_file, interpreter.stdout);
        if (diffOutput !== null) {
            result = TestResult.INTERPRETER_RESULT_DIFFERS;
        }
    }
    return {
        kind: "report",
        report: new TestCaseReport(result, parserExitCode, interpreter.exitCode, parserStdout, parserStderr, interpreter.stdout, interpreter.stderr, diffOutput),
    };
}
//# sourceMappingURL=runner.js.map