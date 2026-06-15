import assert from "node:assert/strict";
import test from "node:test";

import { discountedPrice } from "../src/discount.ts";

test("applies a percentage discount", () => {
  assert.equal(discountedPrice(200, 25), 150);
});

test("supports zero percent", () => {
  assert.equal(discountedPrice(80, 0), 80);
});
