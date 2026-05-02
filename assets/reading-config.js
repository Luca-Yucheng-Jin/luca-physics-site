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
  "d8d0a653348f28f23123938d6315f537dc9f950cc614d8b970563623443cda25";

/* Sentinel: hash of the original shipped default ("change-me"). The
 * page shows a warning banner while PASSPHRASE_HASH equals this value
 * so you notice if you forget to rotate it. */
export const DEFAULT_PASSPHRASE_HASH =
  "e2186dbdb1bb4193608605e84f33208765b5693b55edd4f730a719a100eeea6f";

/* ---------- One-click publish to GitHub ----------
 *
 * The reading.html "Publish" button writes assets/reading-data.json
 * straight to this repo via GitHub's Contents API. GitHub Pages
 * redeploys automatically.
 *
 * To set this up:
 *   1. Visit https://github.com/settings/personal-access-tokens/new
 *      (Settings → Developer settings → Personal access tokens →
 *       Fine-grained tokens → Generate new token).
 *   2. Repository access: Only select repositories → pick this repo.
 *   3. Repository permissions: Contents → Access: Read and write.
 *   4. Pick a short expiration (90 days is reasonable).
 *   5. Click Generate token. Copy the token string (starts with
 *      "github_pat_…"). Paste it into the page when prompted.
 *
 * The token is stored unencrypted in this browser's localStorage. The
 * scope above is the smallest privilege that lets the page commit, so
 * the worst case if the token leaks is someone vandalising this file.
 * Click "Forget token" in the toolbar to clear it.
 */
export const GITHUB_REPO   = "Luca-Yucheng-Jin/luca-physics-site";
export const GITHUB_BRANCH = "main";
export const PUBLISHED_PATH = "assets/reading-data.json";
