#!/usr/bin/env python3
"""
Demonstration script showing citation sentence extraction functionality.
This shows how the extract_citation_sentences function works without requiring a PDF.
"""

from check_hallucinated_references import extract_citation_sentences


def demo_citation_extraction():
    """Demonstrate the citation sentence extraction feature."""
    
    # Example academic paper text
    sample_text = """
Abstract

This paper presents a novel approach to machine learning optimization.

1. Introduction

Recent studies have shown that deep learning techniques are effective [1].
The work by Smith et al. [2] demonstrates significant improvements in accuracy.
Traditional methods [3] have been widely used but have limitations.

Multiple approaches [4], [5], [6] have been proposed to address these challenges.
Our method builds on the foundation laid by previous research [1] and extends it.

2. Related Work

Neural networks have evolved significantly over the past decade [7].
Convolutional architectures [8] and transformers [9] represent major breakthroughs.
The seminal paper by LeCun [7] introduced key concepts that we leverage here.

3. Methodology

We propose a hybrid approach that combines elements from [2] and [8].
As demonstrated in [1], optimization is critical for convergence.

References
[1] A. Smith and B. Jones, "Deep Learning Fundamentals", 2020
[2] J. Smith, M. Brown, and K. Davis, "Advanced Neural Networks", 2021
[3] R. Williams, "Traditional Machine Learning Methods", 2015
[4] L. Chen, "Optimization Techniques Part I", 2019
[5] L. Chen, "Optimization Techniques Part II", 2019
[6] P. Taylor, "Hybrid Approaches", 2020
[7] Y. LeCun, "Convolutional Neural Networks", 2012
[8] A. Krizhevsky, "ImageNet Classification", 2012
[9] A. Vaswani et al., "Attention Is All You Need", 2017
"""
    
    # Find where references section starts
    ref_start = sample_text.find("References")
    
    # Extract citation sentences
    citations = extract_citation_sentences(sample_text, ref_start)
    
    # Display results
    print("=" * 70)
    print("CITATION SENTENCE EXTRACTION DEMONSTRATION")
    print("=" * 70)
    print()
    
    for ref_num in sorted(citations.keys()):
        print(f"Reference [{ref_num}]:")
        print(f"  Cited {len(citations[ref_num])} time(s) in the paper:")
        print()
        for i, sentence in enumerate(citations[ref_num], 1):
            # Clean up the sentence for display
            display_sentence = sentence.strip()
            print(f"  Citation {i}:")
            print(f"    {display_sentence}")
            print()
        print("-" * 70)
        print()
    
    # Summary statistics
    total_refs = len(citations)
    total_citations = sum(len(sents) for sents in citations.values())
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  References cited in text: {total_refs}")
    print(f"  Total citation instances: {total_citations}")
    if total_refs > 0:
        print(f"  Average citations per reference: {total_citations / total_refs:.1f}")
    print()
    
    # Show which reference numbers were cited
    if citations:
        cited_refs = sorted(citations.keys())
        print(f"  Reference numbers cited: {cited_refs}")
        
        # Check if they're sequential starting from 1
        if cited_refs == list(range(1, len(cited_refs) + 1)):
            print(f"  All references (1-{len(cited_refs)}) are cited in the text ✓")
        else:
            print(f"  Note: References are not sequentially numbered from 1")
    print()


if __name__ == "__main__":
    demo_citation_extraction()
