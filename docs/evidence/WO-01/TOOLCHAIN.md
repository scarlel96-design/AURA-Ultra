# 개발 환경 매트릭스
| 항목 | 현재 검증 | API37 전환 후보 |
|---|---|---|
| JDK | 17 | 17 |
| Gradle | 8.11.1 | 9.3.1 |
| AGP | 8.10.1 | 9.1.1 |
| compile/target SDK | 36 | 37 |
| build-tools | 35.0.0 | 36.0.0 |
| Validator | 1.7.0 (최대 WFF5) | 기존 pin 유지 |
| Memory Evaluator | 1.5.1 | 기존 pin 유지 |
| emulator/ADB/RTL | NOT RUN | 공식 API37 이미지, 실제 접근 미확인 |
기준 CI 46000111754. 공식 AGP 9.1.1 호환 표 확인. SDK37 설치와 Gradle 전환은 다음 회차의 별도 CI/회귀로 검증한다. 현재 로컬 사용자 PC 또는 워치 접근 없음. Optimizer 공식 저장소 문서 존재, 실행 NOT RUN.

CI 46001149417: 기존 SDK36/AGP8.10.1에서 WFF2/3/4 APK 및 WFF5 schema-only PASS. API37 후보 자체 실행 NOT RUN.

GPT-02 회차 02 격리 후보: AGP9.1.1, Gradle9.3.1, JDK17, SDK37, build-tools36.0.0. 공식 Gradle distribution SHA-256 b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06, wrapper SHA-256 b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13. CI 결과 PENDING. https://gradle.org/release-checksums/ ; https://developer.android.com/build/releases/agp-9-1-0-release-notes .

회차 02 실제 CI 46002470824 SUCCESS: SDK package platforms;android-37.0 (revision 2), Gradle9.3.1, JDK17.0.21, AGP9.1.1, build-tools36.0.0, 4 Debug APK 검증. SDK37 전환 후보가 자동 빌드 기준으로 검증됨. 실제 기기/optimizer/Release NOT RUN. 첫 실패 CI 46002330942 보존.
