// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract ContributionLedger {
    struct ContributionEvent {
        string nodeId;
        string eventType;
        string objectHash;
        uint256 scoreMilli;
        uint256 creditMilli;
        uint256 createdAt;
    }

    ContributionEvent[] private events_;

    event ContributionRecorded(
        uint256 indexed index,
        string nodeId,
        string eventType,
        string objectHash,
        uint256 scoreMilli,
        uint256 creditMilli
    );

    function recordContribution(
        string calldata nodeId,
        string calldata eventType,
        string calldata objectHash,
        uint256 scoreMilli,
        uint256 creditMilli
    ) external returns (uint256) {
        events_.push(ContributionEvent(nodeId, eventType, objectHash, scoreMilli, creditMilli, block.timestamp));
        uint256 index = events_.length - 1;
        emit ContributionRecorded(index, nodeId, eventType, objectHash, scoreMilli, creditMilli);
        return index;
    }

    function eventCount() external view returns (uint256) {
        return events_.length;
    }

    function getEvent(uint256 index) external view returns (ContributionEvent memory) {
        return events_[index];
    }
}
