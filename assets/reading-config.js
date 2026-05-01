/* Reading-list edit gate.
 *
 *   To set your passphrase:
 *     1. Open /reading.html in a browser.
 *     2. Open the developer console.
 *     3. Run:    await window.ReadingDigest("your-passphrase-here")
 *        It returns a 64-character hex string.
 *     4. Paste that string as the PASSPHRASE_HASH value below.
 *     5. Commit and push reading-config.js.
 *
 *   The default value below is the SHA-256 of the literal string
 *   "change-me". Anyone who reads the source can see this and unlock the
 *   page until you replace it. CHANGE IT before relying on the gate.
 *
 *   This is a soft gate, not real authentication: the hash sits in a
 *   public file, so a weak passphrase can be brute-forced offline. Pick
 *   something with enough entropy (4+ random words) that a dictionary
 *   attack is impractical.
 */
export const PASSPHRASE_HASH =
  "e2186dbdb1bb4193608605e84f33208765b5693b55edd4f730a719a100eeea6f";

/* Sentinel: same hash as the shipped default ("change-me"). The page
 * shows a warning banner while PASSPHRASE_HASH equals this value so you
 * notice if you forget to rotate it. */
export const DEFAULT_PASSPHRASE_HASH =
  "e2186dbdb1bb4193608605e84f33208765b5693b55edd4f730a719a100eeea6f";
