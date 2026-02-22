;nyquist plug-in
;version 4
;type process
;preview enabled
;name "Subliminal"
;debugbutton disabled
;author "Steve Daulton"
;release 2.4.2
;copyright "GNU General Public License v2.0+"

;; License: GPL v2 or later
;; http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
;;
;; An audio frequency AM encoder / decoder for speech.
;; This is a simple form of Steganography (hiding information
;; within another message or physical object). It is a
;; popular method for creating "Silent Subliminals".
;;
;; Disclaimer: The author makes no claims whatsoever regarding
;; the effectiveness or safety of "Silent Subliminals".
;; Copyright Steve Daulton. http://audionyq.com


;control ACTION "Encode or Decode" choice "Encode,Decode" 0


; Global constants
(psetq *cf* 16000     ; Carrier frequency
       *lf* 300       ; Audio-band low frequency
       *hf* 3000      ; Audio-band high frequency
       *enc-gain* 5   ; Encoder gain
       *dec-gain* 4)  ; Decoder gain


(defun audio-filter (sig)
  (setf sig (highpass8 sig *lf*))
  (lowpass8 sig *hf*))


(defun modulate (sig)
  (mult sig (hzosc *cf*)))


(defun sideband-filter (sig)
  (dotimes (i 8 (mult  *enc-gain* sig))
    (setf sig (highpass8 sig (+ *cf* *lf*)))))


(defun encode (sig)
  (setf audio (audio-filter sig))
  (setf modulated (modulate audio))
  (multichan-expand #'limit (sideband-filter modulated)))


(defun decode (sig)
  (setf audio (mult *dec-gain* sig (hzosc *cf*)))
  (setf audio (lowpass8 audio *hf*))
  (multichan-expand #'limit audio))


(defun limit (sig &aux (limit 0.8) (hld 10.0))
  (let* ((time (/ hld 3000.0))  ; lookahead time (seconds)
         (samples (round (* time *sound-srate*)))
         (peak-env (get-env sig samples time limit)))
    (mult sig
      (snd-exp 
        (mult -1 (snd-log peak-env))))))


(defun get-env (sig step lookahead limit)
  (let* ((sig (mult (/ limit) sig))
         (pad-time (* 3 lookahead))       ; padding required at start (seconds)
         (pad-s (* 3 step))               ; padding samples
         (padding (snd-const (peak sig pad-s) 0 *sound-srate* pad-time))
         (peak-env (snd-avg sig (* 4 step) step OP-PEAK)))
    (extract 0 1
      (s-max 1 
        (sim padding
          (at-abs pad-time (cue peak-env)))))))


(cond ((< *sound-srate* 44100) "Error.\nTrack sample rate too low")
      ((= ACTION 0) (encode *track*))
      (t (decode *track*)))
