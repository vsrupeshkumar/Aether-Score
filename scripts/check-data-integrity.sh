#!/bin/bash
# Data integrity check script

set -e

ENVIRONMENT=${1:-development}
ENV_FILE="environments/.env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

echo "Checking data integrity for environment: $ENVIRONMENT"

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set"
    exit 1
fi

cd backend

# Run integrity checks using Python
python3 << EOF
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

from services.validation import DataValidationService

async def main():
    service = DataValidationService()
    results = await service.validate_all_data()
    
    print("\n=== Data Integrity Check Results ===\n")
    
    # Foreign key integrity
    fk_violations = results["foreign_key_integrity"]
    if fk_violations:
        print("❌ Foreign Key Violations Found:")
        for table, violations in fk_violations.items():
            if table != "error":
                print(f"  {table}: {len(violations)} violations")
                for violation in violations[:10]:  # Show first 10
                    print(f"    - {violation}")
                if len(violations) > 10:
                    print(f"    ... and {len(violations) - 10} more")
    else:
        print("✅ No foreign key violations")
    
    # Constraint violations
    constraint_violations = results["constraint_violations"]
    if constraint_violations:
        print("\n❌ Constraint Violations Found:")
        for constraint, violations in constraint_violations.items():
            if constraint != "error":
                print(f"  {constraint}: {len(violations)} violations")
                for violation in violations[:10]:
                    print(f"    - {violation}")
                if len(violations) > 10:
                    print(f"    ... and {len(violations) - 10} more")
    else:
        print("\n✅ No constraint violations")
    
    # Overall status
    print(f"\n{'✅ Data integrity check passed' if results['is_valid'] else '❌ Data integrity check failed'}")
    
    if not results["is_valid"]:
        sys.exit(1)

asyncio.run(main())
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Data integrity check completed successfully"
else
    echo ""
    echo "❌ Data integrity check found violations"
    exit 1
fi

