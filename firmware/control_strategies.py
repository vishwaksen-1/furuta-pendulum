# control_strategies.py
# Control strategy implementations for Furuta Pendulum

import math

# ─────────────────────────────────────────────
#  PD CONTROL STRATEGY
# ─────────────────────────────────────────────
class PDController:
    """
    Traditional proportional-derivative (PD) feedback control.
    Balances pendulum using only φ and φ̇.
    """
    
    def __init__(self, kp=150.0, kd=42.0, k_center=6.0, alpha_max=600.0):
        """
        Initialize PD controller.
        
        Args:
            kp: proportional gain on pendulum angle
            kd: derivative gain on pendulum velocity
            k_center: centering gain coefficient
            alpha_max: maximum control output (rad/s²)
        """
        self.kp = kp
        self.kd = kd
        self.k_center = k_center
        self.alpha_max = alpha_max
        self.name = "PD"
    
    def compute_control(self, phi, phi_dot, theta, theta_dot, centering_mult):
        """
        Compute arm acceleration command.
        
        Args:
            phi: pendulum angle (rad)
            phi_dot: pendulum velocity (rad/s)
            theta: arm angle (rad) - not used in pure PD
            theta_dot: arm velocity (rad/s) - not used in pure PD
            centering_mult: centering ramp multiplier
        
        Returns:
            arm angular acceleration command (rad/s²)
        """
        # PD term: only feedback on pendulum state
        u_pd = self.kp * phi + self.kd * phi_dot
        
        # Centering term: brings arm to center
        u_center = -self.k_center * centering_mult * theta
        
        # Total command, saturated
        u_total = u_pd + u_center
        return max(-self.alpha_max, min(self.alpha_max, u_total))
    
    def __str__(self):
        return (f"PD Controller: Kp={self.kp}, Kd={self.kd}, "
                f"K_center={self.k_center}")


# ─────────────────────────────────────────────
#  LQR CONTROL STRATEGY
# ─────────────────────────────────────────────
class NLPController:
    """
    Nonlinear proportional-derivative control (logarithmic on P term only).
    Applies nonlinear scaling to proportional feedback: u_P = KP*φ*log(|φ|/k1 + 1)
    Derivative term remains linear: u_D = KD*φ̇
    Useful for damping large errors more aggressively near zero.
    """
    
    def __init__(self, kp=200.0, kd=42.0, k_center=6.0, alpha_max=600.0, k1=0.03):
        """
        Initialize nonlinear PD (P-term logarithmic) controller.
        
        Args:
            kp: proportional gain on pendulum angle
            kd: derivative gain on pendulum velocity
            k_center: centering gain coefficient
            alpha_max: maximum control output (rad/s²)
            k1: logarithm scaling parameter (prevents log(0))
        """
        self.kp = kp
        self.kd = kd
        self.k_center = k_center
        self.alpha_max = alpha_max
        self.k1 = k1
        self.name = "NL-P"
    
    def compute_control(self, phi, phi_dot, theta, theta_dot, centering_mult):
        """
        Compute arm acceleration command with nonlinear P feedback.
        
        Args:
            phi: pendulum angle (rad)
            phi_dot: pendulum velocity (rad/s)
            theta: arm angle (rad)
            theta_dot: arm velocity (rad/s) - not used
            centering_mult: centering ramp multiplier
        
        Returns:
            arm angular acceleration command (rad/s²)
        """
        # Nonlinear proportional: only on P term
        u_nl_p = (self.kp * phi) * math.log(abs(phi) / self.k1 + 1)
        
        # Linear derivative term
        u_d = self.kd * phi_dot
        
        # Centering term
        u_center = -self.k_center * centering_mult * theta
        
        # Total command, saturated
        u_total = u_nl_p + u_d + u_center
        return max(-self.alpha_max, min(self.alpha_max, u_total))
    
    def __str__(self):
        return (f"NL-P Controller: Kp={self.kp}, Kd={self.kd}, "
                f"K_center={self.k_center}, k1={self.k1}")


class NLFullController:
    """
    Nonlinear full PD control (logarithmic on entire PD term).
    Applies nonlinear scaling to full feedback: u = (KP*φ + KD*φ̇)*log(|φ|/k1 + 1)
    Both proportional and derivative feedback scaled by the logarithm.
    More aggressive nonlinearity than NL-P.
    """
    
    def __init__(self, kp=200.0, kd=42.0, k_center=6.0, alpha_max=600.0, k1=0.03):
        """
        Initialize nonlinear full PD controller.
        
        Args:
            kp: proportional gain on pendulum angle
            kd: derivative gain on pendulum velocity
            k_center: centering gain coefficient
            alpha_max: maximum control output (rad/s²)
            k1: logarithm scaling parameter (prevents log(0))
        """
        self.kp = kp
        self.kd = kd
        self.k_center = k_center
        self.alpha_max = alpha_max
        self.k1 = k1
        self.name = "NL-Full"
    
    def compute_control(self, phi, phi_dot, theta, theta_dot, centering_mult):
        """
        Compute arm acceleration command with nonlinear full PD feedback.
        
        Args:
            phi: pendulum angle (rad)
            phi_dot: pendulum velocity (rad/s)
            theta: arm angle (rad)
            theta_dot: arm velocity (rad/s) - not used
            centering_mult: centering ramp multiplier
        
        Returns:
            arm angular acceleration command (rad/s²)
        """
        # Nonlinear full PD: entire (KP*φ + KD*φ̇) scaled by log
        u_nl_full = (self.kp * phi + self.kd * phi_dot) * math.log(abs(phi) / self.k1 + 1)
        
        # Centering term
        u_center = -self.k_center * centering_mult * theta
        
        # Total command, saturated
        u_total = u_nl_full + u_center
        return max(-self.alpha_max, min(self.alpha_max, u_total))
    
    def __str__(self):
        return (f"NL-Full Controller: Kp={self.kp}, Kd={self.kd}, "
                f"K_center={self.k_center}, k1={self.k1}")


class LQRController:
    """
    Linear Quadratic Regulator (LQR) state-feedback control.
    Uses full 4D state: [φ, φ̇, θ, θ̇]
    Optimal control minimizing cost: x'Qx + u²R
    """
    
    def __init__(self, k_lqr=None, k_center=6.0, alpha_max=600.0):
        """
        Initialize LQR controller.
        
        Args:
            k_lqr: list [k_phi, k_phi_dot, k_theta, k_theta_dot]
                   If None, uses conservative defaults
            k_center: centering gain coefficient
            alpha_max: maximum control output (rad/s²)
        """
        if k_lqr is None:
            # Conservative defaults: Q=diag(100,10,10,1), R=0.1
            k_lqr = [150.0, 42.0, 6.0, 2.0]
        
        self.k_phi = k_lqr[0]
        self.k_phi_dot = k_lqr[1]
        self.k_theta = k_lqr[2]
        self.k_theta_dot = k_lqr[3]
        self.k_center = k_center
        self.alpha_max = alpha_max
        self.name = "LQR"
    
    def compute_control(self, phi, phi_dot, theta, theta_dot, centering_mult):
        """
        Compute arm acceleration command via LQR state feedback.
        
        Args:
            phi: pendulum angle (rad)
            phi_dot: pendulum velocity (rad/s)
            theta: arm angle (rad)
            theta_dot: arm velocity (rad/s)
            centering_mult: centering ramp multiplier
        
        Returns:
            arm angular acceleration command (rad/s²)
        """
        # LQR state-feedback: u = -K @ [φ, φ̇, θ, θ̇]
        u_lqr = -(self.k_phi * phi + 
                  self.k_phi_dot * phi_dot + 
                  self.k_theta * theta + 
                  self.k_theta_dot * theta_dot)
        
        # Centering term: brings arm to center (same as PD)
        u_center = -self.k_center * centering_mult * theta
        
        # Total command, saturated
        u_total = u_lqr + u_center
        return max(-self.alpha_max, min(self.alpha_max, u_total))
    
    def __str__(self):
        return (f"LQR Controller: K=[{self.k_phi:.1f}, {self.k_phi_dot:.1f}, "
                f"{self.k_theta:.1f}, {self.k_theta_dot:.1f}], "
                f"K_center={self.k_center}")


# ─────────────────────────────────────────────
#  CONTROLLER FACTORY
# ─────────────────────────────────────────────
def get_controller(strategy_name, **kwargs):
    """
    Factory function to instantiate a controller by name.
    
    Args:
        strategy_name: "pd", "lqr", "nl-p", or "nl-full"
        **kwargs: controller-specific parameters
    
    Returns:
        Instantiated controller object
    """
    strategy_name = strategy_name.lower()
    
    if strategy_name == "pd":
        return PDController(
            kp=kwargs.get("kp", 150.0),
            kd=kwargs.get("kd", 42.0),
            k_center=kwargs.get("k_center", 6.0),
            alpha_max=kwargs.get("alpha_max", 600.0)
        )
    
    elif strategy_name == "lqr":
        return LQRController(
            k_lqr=kwargs.get("k_lqr", None),
            k_center=kwargs.get("k_center", 6.0),
            alpha_max=kwargs.get("alpha_max", 600.0)
        )
    
    elif strategy_name == "nl-p":
        return NLPController(
            kp=kwargs.get("kp", 200.0),
            kd=kwargs.get("kd", 42.0),
            k_center=kwargs.get("k_center", 6.0),
            alpha_max=kwargs.get("alpha_max", 600.0),
            k1=kwargs.get("k1", 0.03)
        )
    
    elif strategy_name == "nl-full":
        return NLFullController(
            kp=kwargs.get("kp", 200.0),
            kd=kwargs.get("kd", 42.0),
            k_center=kwargs.get("k_center", 6.0),
            alpha_max=kwargs.get("alpha_max", 600.0),
            k1=kwargs.get("k1", 0.03)
        )
    
    else:
        raise ValueError(f"Unknown control strategy: {strategy_name}")
