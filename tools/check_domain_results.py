"""Validate exact Gradle JUnit test identities and passing evidence."""
import argparse
import os
import re
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
D01_BRANCH = "agent/grok/GB-01-D01"
D01_METHODS = {
    "PayloadIntegrityTest": frozenset((
        "classifiedValueDoesNotPublishAMutablePayload()",
        "cyclicCustomObjectIsRejectedWithoutBeingWalked()",
        "directCursorConstructionRejectsMutablePayload()",
        "higherRevisionStillReplacesEarlierDenial()",
        "mapSetNestedArrayAndCustomPayloadsAreRejected()",
        "mutableListDoesNotReplaceStoredScalarOrChangeDuplicateVerdict()",
        "scalarZeroNullAndDeniedStayAccepted()",
    )),
}

RV01_BRANCH = "agent/grok/GB-01-RV01"
RV01_METHODS = {
    "AuthorityContractTest": frozenset((
        "capabilityConstructionAndCopyCannotForgeAcceptance()",
        "currentIssuedCheckCanGrant()",
        "duplicateAndConflictingCompletionAreHandled()",
        "foreignScopeSessionAndRequestAreRejected()",
        "genericRevisionAndScalarContractRemainIndependent()",
        "invalidateWhileUnknownFencesPendingCheck()",
        "ordinaryDataStatusDoesNotGrantOrRevokeAuthority()",
        "regrantRejectsPriorGeneration()",
        "restartRequiresFreshAuthority()",
        "sameStateCheckDoesNotResurrectInvalidatedGrant()",
        "ticketAndGenerationCeilingsFailClosed()",
        "trustedFailureAndUntrustedInputAreDistinct()",
        "unissuedForeignAndStaleTicketsCannotGrant()",
        "unknownAndDeniedCannotAcquire()",
    )),
}
BRANCH_PROFILES = {D01_BRANCH: "d01", RV01_BRANCH: "rv01"}


def expected_methods(profile):
    if profile not in ("baseline", "d01", "rv01"):
        raise ValueError("Unknown test inventory: " + str(profile))
    expected = dict(BASELINE_METHODS)
    if profile in ("d01", "rv01"):
        if set(expected) & set(D01_METHODS):
            raise ValueError("D01 inventory overlaps the baseline")
        expected.update(D01_METHODS)
    if profile == "rv01":
        if set(expected) & set(RV01_METHODS):
            raise ValueError("RV01 inventory overlaps earlier inventories")
        expected.update(RV01_METHODS)
    return {PREFIX + name: methods for name, methods in expected.items()}


def ci_profile(event, ref, head_ref, head_repo, repository):
    """Select an exact registered branch, never infer from test output."""
    if event == "pull_request":
        if not repository or not head_repo or not head_ref:
            raise ValueError("Missing pull request context")
        if head_repo == repository:
            return BRANCH_PROFILES.get(head_ref, "baseline")
        return "baseline"
    if event in ("push", "workflow_dispatch"):
        if not ref.startswith("refs/heads/"):
            return "baseline"
        return BRANCH_PROFILES.get(ref[len("refs/heads/"):], "baseline")
    raise ValueError("Unsupported CI event: " + str(event))


def counter(root, key):
    value = root.get(key, "")
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError("Invalid suite counter: " + key)
    return int(value)


def verify(directory, profile="baseline"):
    expected = expected_methods(profile)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--profile", choices=("baseline", "d01", "rv01"), default="baseline")
    mode.add_argument("--ci", action="store_true")
    args = parser.parse_args()
    profile = args.profile
    if args.ci:
        profile = ci_profile(
            os.environ.get("GITHUB_EVENT_NAME", ""),
            os.environ.get("GITHUB_REF", ""),
            os.environ.get("GITHUB_HEAD_REF", ""),
            os.environ.get("DOMAIN_HEAD_REPO", ""),
            os.environ.get("GITHUB_REPOSITORY", ""),
        )
    print(f"DOMAIN_INVENTORY {profile}", flush=True)
    print(f"DOMAIN_RESULT {verify(args.directory, profile)} PASS / 0 FAIL / 0 ERROR / 0 SKIP")


if __name__ == "__main__":
    main()
