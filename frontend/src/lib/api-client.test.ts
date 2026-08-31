import { describe, it, expect, beforeEach } from "vitest";
import { setAccessToken, getAccessToken } from "./api-client";

describe("api-client in-memory token state", () => {
  beforeEach(() => {
    setAccessToken(null);
  });

  it("stores and retrieves access token in memory", () => {
    expect(getAccessToken()).toBeNull();
    setAccessToken("test_access_token_123");
    expect(getAccessToken()).toBe("test_access_token_123");
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });
});
