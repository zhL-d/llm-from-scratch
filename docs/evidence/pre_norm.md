#### Step 1, Define Both Architectures Precisely

**Post-Norm** (original *Attention Is All You Need*):

$$
x_{l+1} = \operatorname{Norm}\left(x_l + F_l(x_l)\right)
$$

**Pre-Norm** (modern LLMs):

$$
x_{l+1} = x_l + F_l\left(\operatorname{Norm}(x_l)\right)
$$

The difference is a single repositioning of Norm, but the mathematical consequences are dramatic.

#### Step 2, Compute the Per-Layer Jacobian

This is what backpropagation actually multiplies at each layer.

**Post-Norm.** Let

$$
h_l = x_l + F_l(x_l),
$$

then

$$
x_{l+1} = \operatorname{Norm}(h_l).
$$

By the chain rule:

$$
\frac{\partial x_{l+1}}{\partial x_l}
=
\underbrace{
\frac{\partial \operatorname{Norm}(h_l)}{\partial h_l}
}_{N_l}
\cdot
\underbrace{
(I + J_l)
}_{\text{residual + sublayer}}
=
N_l(I + J_l).
$$

**Pre-Norm.** Let

$$
\hat{x}_l = \operatorname{Norm}(x_l),
$$

then

$$
x_{l+1} = x_l + F_l(\hat{x}_l).
$$

Therefore,

$$
\frac{\partial x_{l+1}}{\partial x_l}
=
\underbrace{I}_{\text{skip}}
+
\underbrace{
J_l^F N_l
}_{\text{sublayer path}}
=
I + J_l^F N_l.
$$

Notation:

$$
J_l
=
\frac{\partial F_l(x_l)}{\partial x_l},
\qquad
J_l^F
=
\frac{\partial F_l}{\partial \hat{x}_l},
\qquad
N_l
=
\frac{\partial \operatorname{Norm}(x_l)}{\partial x_l}.
$$

**The critical structural difference is already visible.**

In pre-norm, the $I$ (skip connection) is naked, multiplied by nothing.

In post-norm, the $I$ is inside the parentheses, so $N_l$ touches everything, including the skip connection.

#### Step 3, Full Gradient: Product Over $L$ Layers

The gradient from the output loss back to layer 1 is a product of $L$ Jacobians.

**Post-Norm:**

$$
g^{(1)}
=
g^{(L)}
\prod_{l=1}^{L}
N_l(I + J_l).
$$

**Pre-Norm:**

$$
g^{(1)}
=
g^{(L)}
\prod_{l=1}^{L}
\left(I + J_l^F N_l\right).
$$

Now expand the pre-norm product:

$$
\prod_{l=1}^{L}
\left(I + J_l^F N_l\right)
=
I
+
\sum_l J_l^F N_l
+
\sum_{l<l'}
J_l^F N_l
J_{l'}^F N_{l'}
+
\ldots
$$

The leading term is $I$.

Even if every $J_l^F$ is small or zero, the gradient still contains a direct identity path from $g^{(L)}$. In other words, the loss gradient can flow backward through the residual stream without being repeatedly transformed by normalization Jacobians.

This is the **gradient highway**.

In post-norm, there is no analogous pure identity path. The $N_l$ matrices are woven throughout the product, including the residual path.