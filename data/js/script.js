'use strict';

(function() {
  let textClosed = 'Показать дополнительные настройки (экстраполяция)';
  let textOpened = 'Скрыть дополнительные настройки (экстраполяция)';
  let collapseButton = document.querySelector('.js-collapse-input');
  let collapseButtonInnerEl = document.querySelector('.js-collapse-input-inner');

  let toggleButtonText = function () {
    if (collapseButton.getAttribute('aria-expanded') === "true") {
      collapseButtonInnerEl.textContent = textClosed;
    } else {
      collapseButtonInnerEl.textContent = textOpened;

    }
  };

  if (collapseButton) {
    collapseButton.addEventListener('click', toggleButtonText);
  }
})();

(function() {
  let descktopSelectSize = '15';
  let tabletSelectSize = '5';
  let countrySelect = document.querySelector('#country');

  let changeSelectSize = function () {
    if (window.innerWidth >= 768) {
      countrySelect.size = descktopSelectSize;
    } else {
      countrySelect.size = tabletSelectSize;
    }
  };

  if (countrySelect) {
    changeSelectSize();

    window.addEventListener('resize', changeSelectSize);

  }
})();

(function() {
  // let descktopSelectSize = '15';
  // let tabletSelectSize = '5';
  let forPeriodInput = document.querySelector('.js-for-period');
  let forPeriodLabel = document.querySelector('.js-for-period ~ span');
  let onPeriodInput = document.querySelector('.js-on-period');
  let onPeriodLabel = document.querySelector('.js-on-period ~ span');

  let cases = {
    sinNom: 'день',
    sinGen: 'дня',
    pluGen: 'дней'
  }

  let modifyLabelNom = function (input, label) {
    if (input.value % 100 >= 11 && input.value % 100 <= 19) {
      label.textContent = cases.pluGen;
    } else {
      switch(input.value % 10) {
        case 1:
          label.textContent = cases.sinNom;
          break;
        case 2:
        case 3:
        case 4:
          label.textContent = cases.sinGen;
          break;
        case 0:
        default: 
          label.textContent = cases.pluGen;
          break;
      };
    }
  };

  let modifyLabelGen = function (input, label) {
    if (input.value % 10 == 1 && input.value % 100 != 11) {
      label.textContent = cases.sinGen;
    } else {
      label.textContent = cases.pluGen;
    }
  };

  if (forPeriodInput && forPeriodLabel) {
    // changeSelectSize();
    forPeriodInput.addEventListener('input', function () {
      modifyLabelNom(forPeriodInput, forPeriodLabel);
    });
  }

  if (onPeriodInput && onPeriodLabel) {
    // changeSelectSize();
    onPeriodInput.addEventListener('input', function () {
      modifyLabelGen(onPeriodInput, onPeriodLabel);
    });
  }
})();