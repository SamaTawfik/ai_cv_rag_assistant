# Suggested Evaluation Questions

Use these as simple starting questions. Before testing, check that each question is actually answerable from your own PDFs. If not, replace it or mark it as an out-of-scope test.

## A. Questions likely to be answerable from the document set

1. What is computer vision?
2. What is the difference between image classification and object detection?
3. What does a bounding box represent in object detection?
4. What is a convolutional neural network (CNN)?
5. What is the role of convolutional layers in a CNN?
6. What is overfitting in deep learning?
7. What is the purpose of a training set and a test set?
8. What is the difference between precision and recall?
9. What is non-maximum suppression (NMS), if it is explained in the PDFs?
10. What are the main stages of an object detection pipeline, if the documents describe them?
11. What is transfer learning, if it is covered in the PDFs?
12. What is the difference between one-stage and two-stage object detectors, if covered?

## B. Questions to test abstention

13. What is the capital of Japan?
14. Who won the FIFA World Cup in 1998?
15. What is the exact current price of a particular stock?

These are out-of-domain examples. The expected behavior is to say that the answer is not available in the provided documents, rather than inventing an answer. If a document unexpectedly contains the answer, choose another out-of-scope question.

## C. Workflow/API checks (not knowledge questions)

16. Submit a blank question to `/ask`. Does validation reject it?
17. Upload a valid PDF. Does the API report successful indexing?
18. Upload a non-PDF file. Is it rejected?
19. Ask a question after uploading a new PDF. Does the new document appear in the returned sources?
20. Does the response include the correct filename and page number?

## What to record for every knowledge question

- Question
- Expected answer / key facts
- Actual answer
- Correct? (Yes / Partial / No)
- Source filename returned
- Page number returned
- Source/page correct? (Yes / No / N/A)
- Abstention expected? (Yes / No)
- Abstention behaved correctly? (Yes / No / N/A)
- Notes (hallucination, missing details, irrelevant retrieval, slow response, etc.)

Do not mark a result correct just because it sounds plausible. Compare it with the source PDF.
