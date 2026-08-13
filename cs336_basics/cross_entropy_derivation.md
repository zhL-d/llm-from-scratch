## Cross Entropy Derivation

$$
cross entropy 
= − log(p(x_{i+1} | x_{1:i}))
$$

$$
= − log(softmax(o_i)_{x_{i+1}})
$$

$$
= -\log\left(
\frac{\exp(o_{i,x_{i+1}})}{\sum_{a=1}^{vocab\_size} \exp(o_{i,a})}
\right)
$$

$$
= \log\left(\sum_{a=1}^{vocab\_size} \exp(o_{i,a})\right) - o_{i,x_{i+1}}
$$

---

### detail

Using log rules:

$$
-\log\left(\frac{A}{B}\right)
= -(\log A - \log B)
= \log B - \log A
$$

Let:

$$
A = \exp(o_{i,x_{i+1}}), \quad
B = \sum_{a=1}^{V} \exp(o_{i,a})
$$

Then:

$$
-\log\left(\frac{A}{B}\right)
= \log(B) - \log(A)
$$

And since:

$$
\log(\exp(x)) = x
$$

We obtain:

$$
-\log\left(\frac{\exp(o_{i,x_{i+1}})}{\sum_{a=1}^{V} \exp(o_{i,a})}\right)
$$

$$
= \log\left(\sum_{a=1}^{V} \exp(o_{i,a})\right) - o_{i,x_{i+1}}
$$
