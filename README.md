# text-to-shape-aws

## This project shows how to build a simple Cloud + AI app using AWS and Python:
•	Takes Free-text Input From User → AWS Bedrock (Claude) → JSON {shape, color}
•	Pillow draws the input by only using "Basic" shapes (circle, square, etc.)
•	Image stored in S3
•	API returns short-lived presigned URL for security
•	Secured with IAM roles, least privilege, input validation, rate limiting, and CloudWatch
• Deployed on EC2 with IAM Role, Security Groups, CloudWatch monitoring

## Architecture
1.	User sends text (/ai-draw endpoint)
2.	Flask app on EC2 calls Bedrock → {shape, color}
3.	Pillow draws image locally
4.	Upload to S3
5.	Return presigned URL (10 min expiry)

## AWS Services Used
- EC2 (Flask API hosting)
- S3 (image storage with presigned URLs)
- IAM Roles (least privilege: S3 + Bedrock only)
- AWS Bedrock (Claude model for NLP → command translation)
- CloudWatch (logs + CPU alarm)
- Security Groups (SSH restricted to my IP, API port limited)

## Notes
- Demo was deployed, tested, and documented with screenshots.
- Environment has been **terminated** to avoid costs (Free Tier project).
- Not done to avoid extra costs but has appropriate base: HTTPS with ALB+ACM, Docker/ECS, Route 53 custom domain.

## Medium Article
👉 [Read the full write-up] -> 
