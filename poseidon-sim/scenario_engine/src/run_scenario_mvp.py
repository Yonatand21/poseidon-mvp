#!/usr/bin/env python3
"""Seed-locked MVP scenario trigger for federated runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Empty


QOS = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


class ScenarioTrigger(Node):
    def __init__(self) -> None:
        super().__init__("scenario_engine_mvp")
        self.declare_parameter("seed", 42)
        self.declare_parameter("drop_after_sec", 8.0)
        self.declare_parameter("metadata_dir", "/recordings")

        self._drop_sent = False
        self._drop_pub = self.create_publisher(Empty, "/coupling/drop_cmd", QOS)
        self._start_ns = self.get_clock().now().nanoseconds
        self._drop_after = float(self.get_parameter("drop_after_sec").value)
        self._seed = int(self.get_parameter("seed").value)
        self._metadata_dir = Path(str(self.get_parameter("metadata_dir").value))
        self._write_metadata()

        self.create_timer(0.2, self._tick)

    def _write_metadata(self) -> None:
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "scenario_id": "mvp_federated_choke_point",
            "seed": self._seed,
            "drop_after_sec": self._drop_after,
        }
        out = self._metadata_dir / "run_metadata.json"
        out.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        self.get_logger().info(f"wrote scenario metadata to {out}")

    def _elapsed(self) -> float:
        return (self.get_clock().now().nanoseconds - self._start_ns) * 1e-9

    def _tick(self) -> None:
        if self._drop_sent:
            return
        if self._elapsed() >= self._drop_after:
            self._drop_pub.publish(Empty())
            self._drop_sent = True
            self.get_logger().info("published /coupling/drop_cmd")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = ScenarioTrigger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main([arg for arg in os.sys.argv[1:]])
