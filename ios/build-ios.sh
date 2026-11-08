#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

CONFIGURATION="${1:-Debug}"

if [[ "$CONFIGURATION" == "Release" ]]; then
  mkdir -p build
  xcodebuild \
    -project PowerLedger.xcodeproj \
    -scheme PowerLedger \
    -configuration Release \
    -destination 'generic/platform=iOS' \
    -archivePath build/PowerLedger.xcarchive \
    archive
  echo "Archive at build/PowerLedger.xcarchive"
  echo "Open Xcode Organizer to export / upload to TestFlight."
else
  xcodebuild \
    -project PowerLedger.xcodeproj \
    -scheme PowerLedger \
    -configuration Debug \
    -sdk iphonesimulator \
    -destination 'generic/platform=iOS Simulator' \
    build
  echo "Simulator build finished."
fi
