import pytest
from unittest.mock import MagicMock
from services.risk_management import RiskManager
from utils.logger import BotLogger

@pytest.fixture
def risk_manager():
    """
    Test Fixture für RiskManager-Instanz
    """
    config = {
        "account_size": 1000.0,
        "risk_per_trade": 1.0,  # 1% des Kontos
        "max_drawdown": 20.0,   # 20% maximaler Verlust
        "max_daily_trades": 10,
        "max_position_size": 200.0,
        "stop_loss_percentage": 5.0,
        "take_profit_percentage": 10.0,
        "min_risk_reward_ratio": 2.0
    }
    logger = BotLogger()
    return RiskManager(logger=logger, config=config)

def test_check_trade_allowed_success(risk_manager):
    """
    Test für erfolgreiche Trade-Prüfung
    """
    result = risk_manager.check_trade_allowed(token="SOL", amount=5, price=30)
    assert result is True

def test_check_trade_allowed_fail_due_to_size(risk_manager):
    """
    Test für Trade, der zu groß ist
    """
    result = risk_manager.check_trade_allowed(token="SOL", amount=10, price=30)
    assert result is False

def test_check_trade_allowed_fail_due_to_daily_limit(risk_manager):
    """
    Test für Überschreiten des täglichen Handelslimits
    """
    risk_manager.daily_stats["total_trades"] = 10
    result = risk_manager.check_trade_allowed(token="SOL", amount=5, price=30)
    assert result is False

def test_check_trade_allowed_fail_due_to_drawdown(risk_manager):
    """
    Test für Erreichen des maximalen Drawdowns
    """
    risk_manager.daily_stats["max_drawdown"] = -200.0
    result = risk_manager.check_trade_allowed(token="SOL", amount=5, price=30)
    assert result is False

def test_calculate_position_size(risk_manager):
    """
    Test für Berechnung der Positionsgröße
    """
    result = risk_manager.calculate_position_size(price=100.0, stop_loss=95.0)
    assert result == pytest.approx(20.0, rel=1e-2)

def test_calculate_position_size_zero_risk(risk_manager):
    """
    Test für Null-Risiko (Preis = Stop Loss)
    """
    result = risk_manager.calculate_position_size(price=100.0, stop_loss=100.0)
    assert result == 0.0

def test_update_trade_stats(risk_manager):
    """
    Test für Aktualisierung der Handelsstatistiken
    """
    # Gewinn-Trade
    risk_manager.update_trade_stats(50.0)
    assert risk_manager.daily_stats["total_trades"] == 1
    assert risk_manager.daily_stats["winning_trades"] == 1
    assert risk_manager.daily_stats["total_pnl"] == 50.0

    # Verlust-Trade
    risk_manager.update_trade_stats(-30.0)
    assert risk_manager.daily_stats["total_trades"] == 2
    assert risk_manager.daily_stats["losing_trades"] == 1
    assert risk_manager.daily_stats["total_pnl"] == 20.0
    assert risk_manager.daily_stats["max_drawdown"] == -30.0

def test_get_stop_loss(risk_manager):
    """
    Test für Stop-Loss-Berechnung
    """
    stop_loss = risk_manager.get_stop_loss(entry_price=100.0)
    assert stop_loss == pytest.approx(95.0, rel=1e-2)

def test_get_take_profit(risk_manager):
    """
    Test für Take-Profit-Berechnung
    """
    take_profit = risk_manager.get_take_profit(entry_price=100.0)
    assert take_profit == pytest.approx(110.0, rel=1e-2)

def test_reset_daily_stats(risk_manager):
    """
    Test für Zurücksetzen der täglichen Handelsstatistiken
    """
    risk_manager.daily_stats["total_trades"] = 5
    risk_manager.daily_stats["total_pnl"] = 100.0
    risk_manager.reset_daily_stats()
    assert risk_manager.daily_stats["total_trades"] == 0
    assert risk_manager.daily_stats["total_pnl"] == 0.0

def test_get_risk_metrics(risk_manager):
    """
    Test für Abruf der Risiko-Metriken
    """
    risk_manager.update_trade_stats(50.0)
    metrics = risk_manager.get_risk_metrics()
    assert metrics["win_rate"] == pytest.approx(100.0, rel=1e-2)
    assert metrics["total_pnl"] == pytest.approx(50.0, rel=1e-2)
    assert metrics["max_drawdown"] == pytest.approx(0.0, rel=1e-2)

def test_check_risk_reward_ratio(risk_manager):
    """
    Test für Überprüfung des Risk/Reward-Verhältnisses
    """
    # Gutes Risk/Reward (1:2)
    trade = {
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0
    }
    assert risk_manager.check_risk_reward_ratio(trade) is True

    # Schlechtes Risk/Reward (1:1)
    trade = {
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 105.0
    }
    assert risk_manager.check_risk_reward_ratio(trade) is False

def test_check_portfolio_exposure(risk_manager):
    """
    Test für Überprüfung der Portfolio-Exposure
    """
    risk_manager.active_positions = [
        {"size": 50.0, "entry_price": 2.0},
        {"size": 30.0, "entry_price": 1.0}
    ]

    # Test innerhalb des Limits
    assert risk_manager.check_portfolio_exposure(
        new_position_size=20.0,
        price=2.0
    ) is True

    # Test über dem Limit
    assert risk_manager.check_portfolio_exposure(
        new_position_size=100.0,
        price=2.0
    ) is False

def test_validate_trade_parameters(risk_manager):
    """
    Test für Validierung der Trade-Parameter
    """
    # Gültige Parameter
    assert risk_manager.validate_trade_parameters(
        price=100.0,
        amount=5.0,
        stop_loss=95.0,
        take_profit=110.0
    ) is True

    # Ungültige Parameter
    assert risk_manager.validate_trade_parameters(
        price=0.0,
        amount=5.0,
        stop_loss=95.0,
        take_profit=110.0
    ) is False

def test_calculate_drawdown(risk_manager):
    """
    Test für Drawdown-Berechnung
    """
    # Setup initial equity
    risk_manager.daily_stats["peak_equity"] = 1000.0
    
    # Test drawdown calculation
    current_equity = 900.0
    drawdown = risk_manager.calculate_drawdown(current_equity)
    assert drawdown == pytest.approx(-10.0, rel=1e-2)  # -10% drawdown