'use strict';

(function() {
  let textClosed = 'Показать дополнительные настройки (экстраполяция)';
  let textOpened = 'Скрыть дополнительные настройки (экстраполяция)';
  let collapseButton = document.querySelector('.js-collapse-input');
  let collapseButtonInnerEl = document.querySelector('.js-collapse-input-inner');
  let collapseBlock = document.querySelector('.collapse');

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
  
  if (collapseBlock) {
    let forseOpening = function () {
      if (collapseBlock.classList.contains('forse-opening')) {
        $('.collapse').collapse('show');
        collapseBlock.classList.remove('forse-opening');
      }
    }

    forseOpening();
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
  let forecConfirmedBlock = document.querySelector('.js-forec-confirmed-block');
  let forecDeathsBlock = document.querySelector('.js-forec-deaths-block');

  let changeHandler = function(allInputs, defaultFunction) {
    if (allInputs[0].checked) {
      allInputs.forEach(function (input, index) {
        if (index !== 0)
        input.disabled = false;        
      });
    } else {
      allInputs.forEach(function (input, index) {
        if (index !== 0)
        input.disabled = true;        
      });
    }
  };
  
  if (forecConfirmedBlock) {;
    let forecConfirmedInputs = forecConfirmedBlock.querySelectorAll('input');

    forecConfirmedInputs[0].addEventListener('change', function() {
      changeHandler(forecConfirmedInputs);
    });  
  }

  if (forecDeathsBlock) {
    let forecDeathsInputs = forecDeathsBlock.querySelectorAll('input');

    forecDeathsInputs[0].addEventListener('change', function() {
      changeHandler(forecDeathsInputs);
    });  
  }

})();

(function() {
  let forPeriodInputs = document.querySelectorAll('.js-for-period');
  let onPeriodInputs = document.querySelectorAll('.js-on-period');
  let periodLabelClass = '.js-period-label';

  let cases = {
    sinNom: 'день',
    sinGen: 'дня',
    pluGen: 'дней'
  }

  let modifyLabelNom = function (input) {
    let label = input.parentElement.querySelector(periodLabelClass);
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

  let modifyLabelGen = function (input) {
    let label = input.parentElement.querySelector(periodLabelClass);
    if (input.value % 10 == 1 && input.value % 100 != 11) {
      label.textContent = cases.sinGen;
    } else {
      label.textContent = cases.pluGen;
    }
  };

  if (forPeriodInputs.length) {
    forPeriodInputs.forEach(element => {
      element.addEventListener('input', function () {
        modifyLabelNom(element);
      });
    });
  }

  if (onPeriodInputs.length) {
    onPeriodInputs.forEach(element => {
      element.addEventListener('input', function () {
        modifyLabelGen(element);
      });
    });
  }
})();