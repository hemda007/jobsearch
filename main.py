"""
Job Search Intelligence Tool

Usage: python main.py

Reads tracker Excel, processes unprocessed rows, fills in match %,
improvement areas, referral profiles, and contextual cold messages.
"""

import sys
import time

import config
import excel_handler
import jd_parser
import matcher
import message_generator
import referral_finder
import resume_parser


def main():
    start_time = time.time()

    # --- Validate setup ---
    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("Create a .env file in the project root with:")
        print("  ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx")
        print("See .env.example for reference.")
        sys.exit(1)

    # --- Step 1: Ensure tracker Excel exists ---
    print(f"Reading tracker: {config.TRACKER_PATH}")
    try:
        unprocessed = excel_handler.read_unprocessed_rows()
    except PermissionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR reading Excel: {e}")
        sys.exit(1)

    if not unprocessed:
        print("No unprocessed rows found.")
        print("To process jobs:")
        print(f"  1. Open the Excel tracker at: {config.TRACKER_PATH}")
        print("  2. Paste a job link in Column A")
        print("  3. Paste the job description text in Column B")
        print("  4. Save the file and run this script again")
        sys.exit(0)

    print(f"Found {len(unprocessed)} unprocessed job(s)...\n")

    # --- Step 2: Parse resume ---
    print("Parsing resume...")
    try:
        resume_data = resume_parser.parse_resume()
        print(f"  Resume loaded: {len(resume_data.get('skills', []))} skills, "
              f"{resume_data.get('experience_years', 'N/A')} experience")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR parsing resume: {e}")
        sys.exit(1)

    # --- Step 3: Process each row ---
    succeeded = []
    failed = []

    with excel_handler.TrackerWriter() as writer:
        for row_num, job_link, jd_text in unprocessed:
            print(f"Processing row {row_num}...")

            try:
                # Parse JD text
                jd_data = jd_parser.parse_jd(jd_text)
                job_title = jd_data.get("job_title", "Unknown")
                company_name = jd_data.get("company_name", "Unknown")
                print(f"  Role: {job_title} at {company_name}")

                time.sleep(config.API_CALL_DELAY)

                # Score match % + get improvements
                match_result = matcher.match_resume_to_jd(resume_data, jd_data, jd_text)
                match_pct = match_result.get("match_percentage", 0)
                improvements = match_result.get("improvements", [])
                print(f"  Match: {match_pct}%")

                # Find referral profiles (uses Google, not Claude — no API delay needed)
                referrals = referral_finder.find_referrals(company_name, job_title)
                real_profiles = sum(1 for r in referrals if r["name"] != "Could not find profile")
                print(f"  Found {real_profiles} referral profile(s)")

                time.sleep(config.API_CALL_DELAY)

                # Generate all messages in a single API call
                messages = message_generator.generate_messages(referrals, resume_data, jd_data)
                print(f"  Generated {len(messages)} message(s)")

                # Write results to Excel (saves after each row)
                results = {
                    "match_percentage": match_pct,
                    "improvements": improvements,
                    "referrals": referrals,
                    "messages": messages,
                }
                writer.write_results(row_num, results)
                print(f"  Saved to Excel\n")

                succeeded.append((row_num, job_title, company_name, match_pct))

            except Exception as e:
                print(f"  ERROR processing row {row_num}: {e}\n")
                failed.append((row_num, str(e)))

    # --- Step 4: Summary ---
    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"Done! Processed {len(succeeded) + len(failed)} job(s) in {elapsed:.0f} seconds.")
    print()

    if succeeded:
        print(f"Succeeded ({len(succeeded)}):")
        for row_num, title, company, pct in succeeded:
            print(f"  Row {row_num}: {title} at {company} — {pct}% match")

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for row_num, error in failed:
            print(f"  Row {row_num}: {error}")

    print(f"\nResults saved to: {config.TRACKER_PATH}")


if __name__ == "__main__":
    main()
