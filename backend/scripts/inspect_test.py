import sys
import scripts.test_real_gemini as test_real_gemini

def inspect():
    print("From test_real_gemini:")
    print("RecoveryActionType ID:", id(test_real_gemini.RecoveryActionType))
    print("RecoveryActionType members:", list(test_real_gemini.RecoveryActionType))
    
if __name__ == "__main__":
    inspect()
