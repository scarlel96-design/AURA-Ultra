"""Validate exact Gradle JUnit test identities and passing evidence."""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PREFIX = "io.github.scarlel96.aura.domain."
# Match the approved Kotlin @Test methods and preserved GB-01 R02 XML.
# Update this contract when approved Domain tests change.
BASELINE_METHODS = {
    "DraftContractTest": frozenset((
        "blankLocationIsRejected()",
        "blankReasonCodeIsRejected()",
        "contextBlankTokenIsRejectedAndZeroCharacterStaysOpaque()",
        "contextDraftDoesNotDefaultMissingAxes()",
        "forecastWindowIsSeparateFromObservedAt()",
        "invertedAndEmptyValidityWindowsFail()",
        "missingRainStaysNull()",
        "nestedInvalidObservationFailsTheDraft()",
        "observedAndForecastRainStayDistinctIncludingZero()",
        "presentationRevisionZeroIsDistinctFromNull()",
        "probabilityKindIsNotRewritten()",
        "wrongRainKindIsReportedAndNotCoerced()",
    )),
    "FreshnessTest": frozenset((
        "boundaryIsExpiredAtOrAfter()",
        "callerReferenceTimeDecidesFreshnessWithoutAClock()",
        "errorDeniedAndUnavailableAreNotRewrittenWhenExpired()",
        "expiredValidBecomesStaleCopyAndKeepsPayload()",
        "freshDeniedDoesNotBecomeValid()",
        "instantMaxBoundary()",
        "lateArrivalBeforeObservedExpiryRemainsValid()",
        "sameInstantFromDifferentZonesHasOneFreshness()",
        "staleIsNotPromotedWhenStillInsideWindow()",
        "structurallyInvalidInputIsNotDegraded()",
        "undeclaredExpiryDoesNotBecomeStaleOrImmortalClaim()",
    )),
    "IdentityTest": frozenset((
        "sourceIdIsCaseSensitiveAndDoesNotTrim()",
        "sourceIdKeepsCanonicalToken()",
        "sourceIdRejectsBlankWhitespaceAndControl()",
        "subjectAcceptsUnnormalizedKoreanToken()",
        "subjectRejectsBlankAndPaddedToken()",
    )),
    "PipelineTest": frozenset((
        "corruptUnitDoesNotReplaceStoredReading()",
        "deniedErrorAndStaleAreNotPresentedAsFreshValidReadings()",
        "deniedStreamRejectsALaterZeroForgery()",
        "undeclaredTtlStaysDistinctFromFresh()",
        "zeroReadingExpiresWithoutBecomingMissing()",
    )),
    "RevisionGateTest": frozenset((
        "blankSubjectKeyIsRejected()",
        "equalRevisionWithDifferentPayloadDoesNotOverwrite()",
        "equalRevisionWithOnlyReceiveTimeChangedIsDuplicate()",
        "firstValidRevisionIsAccepted()",
        "higherRevisionReplacesAndGapIsAllowed()",
        "invalidIncomingDoesNotCreateOrReplaceCursor()",
        "keyMismatchKeepsTheCurrentStream()",
        "maxLongRevisionDuplicateAndPredecessor()",
        "negativeRevisionsCompareNumerically()",
        "negativeZeroIsNotTreatedAsTheSamePayload()",
        "newerRevisionWithEarlierReceiveTimeIsAcceptedAndFlagged()",
        "olderRevisionDoesNotReplaceCurrent()",
        "outOfOrderSequenceKeepsTheNewestRevision()",
        "sourceInsideObservationMustMatchKey()",
        "wrongUnitDoesNotPassTheGate()",
    )),
    "SourceScanTest": frozenset((
        "mainSourcesStayFreeOfPlatformClockAndNetwork()",
    )),
    "ValidationTest": frozenset((
        "absentValueSkipsExpectedUnit()",
        "absentValueStillSkipsUnitCharacterChecks()",
        "actualZeroStaysAReading()",
        "allKindsRemainUnchangedByValidation()",
        "blankOrPaddedUnitIsRejectedWhenValueExists()",
        "conflictingRangesAreRejectedBeforeComparison()",
        "deniedAndErrorWithoutValueStayDistinct()",
        "doubleRangeBoundaries()",
        "equalReferenceTimeIsNotFuture()",
        "exclusiveAdjacentLongRangeIsEmpty()",
        "exclusiveDoubleBoundsRejectEndpoints()",
        "exclusiveExtremeWithNoRepresentableLongIsEmpty()",
        "exclusiveLongEndpointAndMaxValue()",
        "exclusiveNeighborAndExtremeInclusivePointsStayValid()",
        "expiryBeforeObservedAtIsStructural()",
        "futureTimestampsStayUncheckedUnlessCallerSelectsPolicy()",
        "injectedDeniedAndUnavailableNumbersAreRejected()",
        "injectedErrorZeroIsNotAcceptedOrCoerced()",
        "internalWhitespaceInUnitIsRejectedEvenWhenExpectedMatches()",
        "internalWhitespaceThatIsAlsoAControlCharacterIsRejected()",
        "longRangeAcceptsIntExactlyAndRejectsDouble()",
        "malformedRangesAreRejected()",
        "missingValueIsUnavailableAndNotZero()",
        "negativeZeroIsAnActualReadingAndIsNotCanonicalized()",
        "nonFiniteFloatsAreRejectedWithoutBecomingZero()",
        "nonWhitespaceControlCharacterInUnitIsRejected()",
        "plainUnitTokensStayAccepted()",
        "singlePointRangeAcceptsOnlyThatPoint()",
        "staleZeroRemainsAStaleReading()",
        "textualZeroIsNotTreatedAsMissing()",
        "unitMatchIsExactAndDoesNotConvert()",
        "validOrStaleWithoutValueIsRejectedAndNotRewritten()",
    )),
}
BASELINE = {name: len(methods) for name, methods in BASELINE_METHODS.items()}


def counter(root, key):
    value = root.get(key, "")
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError("Invalid suite counter: " + key)
    return int(value)


def verify(directory):
    expected = {PREFIX + name: methods for name, methods in BASELINE_METHODS.items()}
    seen = set()
    total = 0
    for path in sorted(directory.glob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            raise ValueError("Invalid JUnit XML: " + str(path)) from exc
        name = root.get("name")
        if root.tag != "testsuite" or name not in expected or name in seen:
            raise ValueError("Unknown or duplicate suite: " + str(name))
        if path.name != "TEST-" + name + ".xml":
            raise ValueError("Suite filename mismatch: " + str(path))
        cases = root.findall("testcase")
        if counter(root, "tests") != len(cases) or len(cases) != len(expected[name]):
            raise ValueError("Invalid test count: " + name)
        if any(counter(root, key) != 0 for key in ("failures", "errors", "skipped")):
            raise ValueError("Nonpassing suite: " + name)
        metadata = set()
        for child in root:
            if child.tag == "testcase":
                continue
            if child.tag not in {"properties", "system-out", "system-err"} or child.tag in metadata:
                raise ValueError("Invalid suite child: " + child.tag)
            metadata.add(child.tag)
            if child.tag == "properties":
                if any(prop.tag != "property" or len(prop) for prop in child):
                    raise ValueError("Invalid suite properties")
            elif len(child):
                raise ValueError("Nested suite log element")
        methods = set()
        for case in cases:
            method = case.get("name")
            if case.get("classname") != name or method not in expected[name] or method in methods:
                raise ValueError("Invalid or duplicate test identity: " + str(method))
            if len(case):
                raise ValueError("Nonpassing or nested testcase: " + str(method))
            methods.add(method)
        if methods != expected[name]:
            raise ValueError("Missing baseline test identity: " + name)
        seen.add(name)
        total += len(methods)
    if seen != set(expected):
        raise ValueError("Missing baseline suites: " + str(sorted(set(expected) - seen)))
    return total


if __name__ == "__main__":
    print(f"DOMAIN_RESULT {verify(Path(sys.argv[1]))} PASS / 0 FAIL / 0 ERROR / 0 SKIP")
