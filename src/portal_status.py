"""
portal_status.py — fasalrin.gov.in KCC Application Status Checker
──────────────────────────────────────────────────────────────────
Detects whether a farmer's loan application is:
  fresh     → no prior application; proceed with normal form fill
  draft     → application started but Review & Submit not done yet
  submitted → IS/PRI claim already created (Activity saved or fully submitted)

Kept entirely separate from PR_V4.py so draft logic can evolve on its own.

Usage in PR_V4.py:
    from portal_status import check_portal_status, resume_draft, DraftRecord, SubmittedRecord
"""

# ── Draft keyword signals ─────────────────────────────────────────────────────
# Appear as toast/inline text when the farmer has a partially-saved application.
# All matches are case-insensitive.
DRAFT_KEYWORDS = [
    "application already in progress",
    "application in progress",
    "draft application",
    "application saved as draft",
    "saved as draft",
    "draft saved",
    "incomplete application",
    "resume application",
    "continue application",
    "draft already exists",
    "edit draft",
]

# Button labels that indicate a draft "Resume / Edit" option.
# Exact upper-case match so we don't catch unrelated buttons.
DRAFT_BUTTON_TEXTS = [
    "EDIT DRAFT",
    "RESUME DRAFT",
    "RESUME APPLICATION",
    "CONTINUE DRAFT",
    "CONTINUE APPLICATION",
]

# ── Submitted keyword signals ─────────────────────────────────────────────────
# These appear when the IS/PRI claim has been created (Activity tab saved or
# final submit done). Must be SPECIFIC phrases — not bare "IS/PRI" or "Claim"
# which also appear in the portal's navigation menu sidebar.
SUBMITTED_KEYWORDS = [
    "already been submitted",
    "already submitted",
    "submit the Claim",
    "Interest Cycle",
    "IS/PRI Claim has",
    "IS/PRI claim already",
    "claim has already been",
    "You have already submitted",
    "application has been submitted",
]


# ── Exception classes ─────────────────────────────────────────────────────────

class DraftRecord(Exception):
    """Application exists in draft state on the portal (not yet submitted)."""
    pass


class SubmittedRecord(Exception):
    """IS/PRI claim already exists — application fully or partially submitted."""
    pass


# ── Internal helpers ──────────────────────────────────────────────────────────

def _dismiss_error_toast(driver):
    """Click the first visible close/dismiss element — coordinate-free."""
    driver.execute_script("""
        var sel = '[class*="close"],[class*="dismiss"],'
                + '[aria-label="Close"],[aria-label="close"],[data-dismiss]';
        var els = document.querySelectorAll(sel);
        for (var i = 0; i < els.length; i++) {
            if (els[i].offsetParent) { els[i].click(); return; }
        }
    """)


# ── Public API ────────────────────────────────────────────────────────────────

def check_portal_status(driver):
    """
    Scan visible page content for draft or submitted signals.

    Call this after the Activity tab has loaded (right after Financial Details
    SAVE & CONTINUE) and before attempting ADD / activity form fill.

    Key design:
      - Does NOT scan broad div/span/p tags — those include the nav sidebar
        which always contains "IS/PRI Claim Application" as a menu link.
      - Does NOT use bare keywords "IS/PRI" or "Claim" — too generic.
      - Skips elements inside nav / aside / header / sidebar containers.
      - Only trusts specific error/toast/modal class elements.

    Raises:
        DraftRecord      if a draft application is detected.
        SubmittedRecord  if an already-submitted (IS/PRI) record is detected.
    Returns:
        None             if the application looks fresh — caller may proceed.
    """
    result = driver.execute_script(
        """
        var DRAFT_KEYS  = arguments[0];
        var DRAFT_BTNS  = arguments[1];
        var SUBMIT_KEYS = arguments[2];

        // ── Only scan elements that are actual error/toast/modal containers.
        // Deliberately excludes div/p/span/h* to avoid false positives from
        // the portal navigation sidebar (which always shows "IS/PRI Claim
        // Application" as a menu item).
        var nodes = document.querySelectorAll(
            '[class*="toast"],[class*="alert"],[class*="error"],[class*="warning"],'
          + '[class*="notification"],[class*="popup"],[class*="modal"],'
          + '[class*="snack"],[class*="banner"],[class*="flash"],'
          + 'mat-snack-bar-container,mat-dialog-container'
        );

        var draftMatch     = null;
        var submittedMatch = null;

        for (var i = 0; i < nodes.length; i++) {
            var el = nodes[i];
            if (el.offsetParent === null) continue;          // hidden element

            // Skip anything inside nav / sidebar / header — those areas show
            // menu links that match our keywords (e.g. "IS/PRI Claim Application").
            if (el.closest) {
                var nav = el.closest(
                    'nav, aside, header, [class*="sidebar"], '
                  + '[class*="nav-wrap"], [class*="left-menu"], '
                  + '[role="navigation"], [class*="breadcrumb"]');
                if (nav) continue;
            }

            var t  = (el.textContent || '').trim();
            if (t.length < 8 || t.length > 500) continue;   // too short / is a whole page
            var tl = t.toLowerCase();

            if (!draftMatch) {
                for (var d = 0; d < DRAFT_KEYS.length; d++) {
                    if (tl.indexOf(DRAFT_KEYS[d].toLowerCase()) >= 0) {
                        draftMatch = t.slice(0, 200); break;
                    }
                }
            }
            if (!submittedMatch) {
                for (var s = 0; s < SUBMIT_KEYS.length; s++) {
                    if (t.indexOf(SUBMIT_KEYS[s]) >= 0) {
                        submittedMatch = t.slice(0, 200); break;
                    }
                }
            }
            if (draftMatch && submittedMatch) break;
        }

        // Also scan visible button text for draft resume / edit buttons.
        // Buttons are NOT in the nav sidebar so safe to scan globally.
        if (!draftMatch) {
            var btns = document.querySelectorAll('button');
            for (var b = 0; b < btns.length; b++) {
                if (btns[b].offsetParent === null) continue;
                var bt = (btns[b].textContent || '').trim().toUpperCase();
                for (var db = 0; db < DRAFT_BTNS.length; db++) {
                    if (bt === DRAFT_BTNS[db]) {
                        draftMatch = 'Draft button: ' + bt; break;
                    }
                }
                if (draftMatch) break;
            }
        }

        // Draft takes priority — safer to mis-classify submitted as draft.
        if (draftMatch)     return ['draft',     draftMatch];
        if (submittedMatch) return ['submitted', submittedMatch];
        return null;
        """,
        DRAFT_KEYWORDS,
        DRAFT_BUTTON_TEXTS,
        SUBMITTED_KEYWORDS,
    )

    if result is None:
        return  # fresh record — caller proceeds normally

    status, msg = result[0], result[1]
    _dismiss_error_toast(driver)

    if status == "draft":
        raise DraftRecord(msg)
    raise SubmittedRecord(msg)


def resume_draft(driver):
    """
    Click the RESUME / EDIT DRAFT button on a draft application popup.

    Returns:
        str   button text that was clicked, e.g. "EDIT DRAFT"
        None  if no resume button was found
    """
    return driver.execute_script("""
        var candidates = [
            'EDIT DRAFT','RESUME DRAFT','RESUME APPLICATION',
            'CONTINUE DRAFT','CONTINUE APPLICATION','RESUME','EDIT'
        ];
        var btns = document.querySelectorAll('button');
        for (var b = 0; b < btns.length; b++) {
            if (btns[b].offsetParent === null) continue;
            var bt = (btns[b].textContent || '').trim().toUpperCase();
            for (var c = 0; c < candidates.length; c++) {
                if (bt === candidates[c]) {
                    btns[b].click();
                    return bt;
                }
            }
        }
        return null;
    """)
