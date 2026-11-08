# Main study analysis

Model: qwen2.5:14b-instruct

## H1: full replanning vs local repair (success)
- McNemar exact: full-only wins b=22, repair-only wins c=52, p=0.0006 (Holm 0.0013)
- Risk difference (full - repair): sev1 -0.10 CI-0.18..-0.03 | sev3 -0.10 CI-0.17..-0.02

## H2: does the advantage grow with severity (interaction)
- Logistic strat:sev coef -0.057, p=0.8249 (Holm 0.8249)
- Interaction as difference of risk differences (sev3 - sev1): +0.01 CI-0.10..+0.11  [estimation-based backup]

## Logistic model
```
                           Logit Regression Results                           
==============================================================================
Dep. Variable:                success   No. Observations:                  588
Model:                          Logit   Df Residuals:                      584
Method:                           MLE   Df Model:                            3
Date:                Sat, 07 Nov 2026   Pseudo R-squ.:                 0.02138
Time:                        20:36:01   Log-Likelihood:                -371.46
converged:                       True   LL-Null:                       -379.57
Covariance Type:              cluster   LLR p-value:                  0.001016
==============================================================================
                 coef    std err          z      P>|z|      [0.025      0.975]
------------------------------------------------------------------------------
Intercept     -0.2412      0.143     -1.686      0.092      -0.522       0.039
strat         -0.4445      0.164     -2.705      0.007      -0.767      -0.122
sev           -0.5659      0.266     -2.127      0.033      -1.087      -0.045
strat:sev     -0.0567      0.256     -0.221      0.825      -0.559       0.446
==============================================================================
```

