import json
from working_json_animator import create_working_animation_from_json


def run_tests():
    tests = [
        # Riemann sums
        {
            'name': 'Riemann polynomial',
            'json': {
                'type': 'riemann_sum',
                'function': 'x^2 + 2*x - 1',
                'domain': [0, 3],
                'options': {'sum_type': 'right', 'num_rectangles': 12}
            }
        },
        {
            'name': 'Riemann trig',
            'json': {
                'type': 'riemann_sum',
                'function': 'sin(x)',
                'domain': [0, 3.14],
                'options': {'sum_type': 'left', 'num_rectangles': 16}
            }
        },
        {
            'name': 'Riemann rational (safe domain)',
            'json': {
                'type': 'riemann_sum',
                'function': '1/x',
                'domain': [1, 5],
                'options': {'sum_type': 'right', 'num_rectangles': 20}
            }
        },
        {
            'name': 'Riemann log (safe domain)',
            'json': {
                'type': 'riemann_sum',
                'function': 'log(x)',
                'domain': [0.1, 5],
                'options': {'sum_type': 'right', 'num_rectangles': 15}
            }
        },
        {
            'name': 'Riemann damped trig',
            'json': {
                'type': 'riemann_sum',
                'function': 'exp(-x)*sin(2*x)',
                'domain': [0, 6.28],
                'options': {'sum_type': 'left', 'num_rectangles': 24}
            }
        },
        {
            'name': 'Riemann sqrt (safe domain)',
            'json': {
                'type': 'riemann_sum',
                'function': 'sqrt(x)',
                'domain': [0, 4],
                'options': {'sum_type': 'right', 'num_rectangles': 12}
            }
        },
        # Derivatives
        {
            'name': 'Derivative cubic',
            'json': {
                'type': 'derivative',
                'function': 'x^3 - 3*x',
                'domain': [-3, 3],
                'options': {'point': 1.0}
            }
        },
        {
            'name': 'Derivative damped trig',
            'json': {
                'type': 'derivative',
                'function': 'exp(-x)*sin(2*x)',
                'domain': [0, 6.28],
                'options': {'point': 2.0}
            }
        },
        {
            'name': 'Derivative tan (safe domain)',
            'json': {
                'type': 'derivative',
                'function': 'tan(x)',
                'domain': [0, 1],
                'options': {'point': 0.7}
            }
        },
        # Linear system
        {
            'name': 'Linear system (2 eqs)',
            'json': {
                'type': 'linear_system',
                'domain': [-2, 5],
                'options': {'equations': ['y = 2*x + 1', 'y = -x + 4']}
            }
        },
        # Linear implicit
        {
            'name': 'Linear system implicit (ax+by=c)',
            'json': {
                'type': 'linear_system',
                'domain': [-5, 5],
                'options': {'equations': ['2*x + y = 5', '-x + 2*y = 4']}
            }
        },
        # Integrals
        {
            'name': 'Integral polynomial',
            'json': {
                'type': 'integral',
                'function': 'x^2 + 2*x - 1',
                'domain': [0, 3],
                'options': {}
            }
        },
        {
            'name': 'Integral trig',
            'json': {
                'type': 'integral',
                'function': 'sin(x)',
                'domain': [0, 3.14],
                'options': {}
            }
        },
        {
            'name': 'Integral exp damped',
            'json': {
                'type': 'integral',
                'function': 'exp(-x)*sin(2*x)',
                'domain': [0, 6.28],
                'options': {}
            }
        },
        # Equation display
        {
            'name': 'Equation display (single)',
            'json': {
                'type': 'equation',
                'function': r"y = x^2 + 2x - 1",
                'domain': [0, 1],
                'options': {}
            }
        },
        {
            'name': 'Equation display (multiple)',
            'json': {
                'type': 'equation_display',
                'domain': [0, 1],
                'options': {
                    'equations': [r"y = 2x + 1", r"y = -x + 4", r"f(x) = e^{-x} \sin(2x)"]
                }
            }
        },
    ]

    results = []
    print('Running JSON-driven animation tests...')
    for t in tests:
        name = t['name']
        print(f"\n▶ {name}")
        success, anim_id, file_path = create_working_animation_from_json(t['json'])
        print('  success:', success)
        print('  id     :', anim_id)
        print('  file   :', file_path)
        results.append((name, success, file_path))

    print('\nSummary:')
    passed = 0
    for name, success, file_path in results:
        status = '✅' if success else '❌'
        if success:
            passed += 1
        print(f"  {status} {name}: {file_path}")
    print(f"\nPassed {passed}/{len(results)}")


if __name__ == '__main__':
    run_tests()
