
import math

def LearningRateSchedule(t: int, alpha_max: float, alpha_min: float, t_w: int, t_c: int) -> float:
    """
    Cosine annealing learning rate schedule
    
    :param t: The current step
    :type t: int
    :param alpha_max: The maximum learning rate
    :type alpha_max: float
    :param alpha_min: The minimum (final) learning rate 
    :type alpha_min: float
    :param t_w: The number of warm-up iterations
    :type t_w: int
    :param t_c: The number of cosine annealing iterations
    :type t_c: int
    :return: The learning rate to use for the gradient update at step t
    :rtype: float
    """
    if t < t_w:
        return (t / t_w) * alpha_max
    if t_w <= t <= t_c:
        return alpha_min + 1/2 * (1 + math.cos(((t - t_w) / (t_c - t_w)) * math.pi)) * (alpha_max - alpha_min)
    if t > t_c:
        return alpha_min
