# Security Scans

## git-secrets

```shell
brew install git-secrets

git-secrets --register-aws
git-secrets --scan -r
git-secrets --scan-history
    found #env=cdk.Environment(account='123456789012', region='us-east-1'),

git secrets --add --allowed --literal '123456789012'
```

## bandit

```shell
pip install bandit

bandit --ini .bandit -r  &> security.bandit.out
```

## cdk-nag

```shell
cdk synth
```
