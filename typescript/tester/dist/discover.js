/**
 * @file discover.ts
 * @brief This model is responsible for finding and loading tests. Looks for tests (.test-files)
 * Set type of test, find .in and .out files and create TestCaseDefinition objects.
 * @author Martin Turčan <xturcam@vutbr.cz>
 */
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join, basename } from "node:path";
import { TestCaseDefinition, TestCaseDefinitionFile, TestCaseType, UnexecutedReason, UnexecutedReasonCode, } from "./models.js";
/**
 * @brief parse .test file
 * @param filePath path to .test file
 * @returns TestDataHeader object with parsed data
 */
function parseTestFile(filePath) {
    const content = readFileSync(filePath, "utf-8");
    const lines = content.split(/\r?\n/);
    const data = {
        description: null,
        category: null,
        points: null,
        sourceCode: "",
        expectedParserCode: [],
        expectedInterpreterCode: [],
    };
    let i = 0;
    while (i < lines.length) {
        const line = lines[i] ?? "";
        if (line.trim() === "") {
            // Empty line indicates end of header
            i++;
            break;
        }
        if (line.startsWith("***")) {
            data.description = line.slice(4).trim();
        }
        else if (line.startsWith("+++")) {
            data.category = line.slice(4).trim();
        }
        else if (line.startsWith(">>>")) {
            const pointsStr = parseFloat(line.slice(4).trim());
            if (!isNaN(pointsStr))
                data.points = pointsStr;
        }
        else if (line.startsWith("!C! ")) {
            const code = parseInt(line.slice(4).trim(), 10);
            if (!isNaN(code))
                data.expectedParserCode.push(code);
        }
        else if (line.startsWith("!I! ")) {
            const code = parseInt(line.slice(4).trim(), 10);
            if (!isNaN(code))
                data.expectedInterpreterCode.push(code);
        }
        i++;
    }
    data.sourceCode = lines.slice(i).join("\n");
    return data;
}
/**
 * @bief determine type of test case based on expected parser and interpreter codes
 * @param testData TestDataHeader object with parsed data from .test file
 * @returns TestCaseType or null
 */
function determineTestCaseType(testData) {
    const hasParserCodes = testData.expectedParserCode.length > 0;
    const hasInterpreterCodes = testData.expectedInterpreterCode.length > 0;
    if (hasParserCodes && hasInterpreterCodes)
        return TestCaseType.COMBINED;
    if (hasParserCodes && !hasInterpreterCodes)
        return TestCaseType.PARSE_ONLY;
    if (!hasParserCodes && hasInterpreterCodes)
        return TestCaseType.EXECUTE_ONLY;
    return null;
}
/**
 * @brief look through testDir and find all .test files and parse them
 * @param testsDir absolut path to directory with tests
 * @param recursive if true look for .test files in subdirectories as well
 * @returns DiscoveryResult with discovered tests and unexecuted tests
 */
export function discoverTests(testsDir, recursive) {
    const discovered = [];
    const unexecuted = {};
    const testFiles = findTestFiles(testsDir, recursive);
    for (const file of testFiles) {
        const name = basename(file, ".test");
        //look for .in and .out
        const dir = file.slice(0, file.length - basename(file).length);
        const inFile = join(dir, `${name}.in`);
        const outFile = join(dir, `${name}.out`);
        //TestCaseDefinitionFile holds only paths
        const fileModel = new TestCaseDefinitionFile({
            name,
            test_source_path: file,
            stdin_file: existsSync(inFile) ? inFile : null,
            expected_stdout_file: existsSync(outFile) ? outFile : null,
        });
        //parse .test file
        let data;
        try {
            data = parseTestFile(file);
        }
        catch {
            unexecuted[name] = new UnexecutedReason(UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE, `Failed to parse test file: ${file}`);
            continue;
        }
        //validate required fields
        if (data.category === null) {
            unexecuted[name] = new UnexecutedReason(UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE, `Missing required category in test file: ${file}`);
            continue;
        }
        if (data.points === null) {
            unexecuted[name] = new UnexecutedReason(UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE, `Missing required points in test file: ${file}`);
            continue;
        }
        //determine type of test case
        const testType = determineTestCaseType(data);
        if (testType === null) {
            unexecuted[name] = new UnexecutedReason(UnexecutedReasonCode.CANNOT_DETERMINE_TYPE, `Cannot determine test case type for file: ${file}`);
            continue;
        }
        //create TestCaseDefinition and validate exit codes based on type
        try {
            const def = new TestCaseDefinition({
                name: fileModel.name,
                test_source_path: fileModel.test_source_path,
                stdin_file: fileModel.stdin_file,
                expected_stdout_file: fileModel.expected_stdout_file,
                test_type: testType,
                description: data.description,
                category: data.category,
                points: data.points,
                expected_parser_exit_codes: data.expectedParserCode.length > 0 ? data.expectedParserCode : null,
                expected_interpreter_exit_codes: data.expectedInterpreterCode.length > 0 ? data.expectedInterpreterCode : null,
            });
            discovered.push(def);
        }
        catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            unexecuted[name] = new UnexecutedReason(UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE, `Invalid test definition: ${msg}`);
        }
    }
    return { discovered, unexecuted };
}
/**
 * @brief find all .test files in the given directory (and subdirectories if recursive is true)
 * @param dir directory to search
 * @param recursive if true search in subdirectories as well
 * @returns alphabetically sorted array of paths to .test files
 */
function findTestFiles(dir, recursive) {
    const results = [];
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const fullPath = join(dir, entry.name);
        if (entry.isDirectory() && recursive) {
            results.push(...findTestFiles(fullPath, recursive));
        }
        else if (entry.isFile() && entry.name.endsWith(".test")) {
            results.push(fullPath);
        }
    }
    return results.sort();
}
//# sourceMappingURL=discover.js.map