// Generated from norwegian.sbl by Snowball 3.0.1 - https://snowballstem.org/

/**@constructor*/
var NorwegianStemmer = function() {
    var base = new BaseStemmer();

    /** @const */ var a_0 = [
        ["", -1, 1],
        ["ind", 0, -1],
        ["kk", 0, -1],
        ["nk", 0, -1],
        ["amm", 0, -1],
        ["omm", 0, -1],
        ["kap", 0, -1],
        ["skap", 6, 1],
        ["pp", 0, -1],
        ["lt", 0, -1],
        ["ast", 0, -1],
        ["\u00F8st", 0, -1],
        ["v", 0, -1],
        ["hav", 12, 1],
        ["giv", 12, 1]
    ];

    /** @const */ var a_1 = [
        ["a", -1, 1],
        ["e", -1, 1],
        ["ede", 1, 1],
        ["ande", 1, 1],
        ["ende", 1, 1],
        ["ane", 1, 1],
        ["ene", 1, 1],
        ["hetene", 6, 1],
        ["erte", 1, 4],
        ["en", -1, 1],
        ["heten", 9, 1],
        ["ar", -1, 1],
        ["er", -1, 1],
        ["heter", 12, 1],
        ["s", -1, 3],
        ["as", 14, 1],
        ["es", 14, 1],
        ["edes", 16, 1],
        ["endes", 16, 1],
        ["enes", 16, 1],
        ["hetenes", 19, 1],
        ["ens", 14, 1],
        ["hetens", 21, 1],
        ["ers", 14, 2],
        ["ets", 14, 1],
        ["et", -1, 1],
        ["het", 25, 1],
        ["ert", -1, 4],
        ["ast", -1, 1]
    ];

    /** @const */ var a_2 = [
        ["dt", -1, -1],
        ["vt", -1, -1]
    ];

    /** @const */ var a_3 = [
        ["leg", -1, 1],
        ["eleg", 0, 1],
        ["ig", -1, 1],
        ["eig", 2, 1],
        ["lig", 2, 1],
        ["elig", 4, 1],
        ["els", -1, 1],
        ["lov", -1, 1],
        ["elov", 7, 1],
        ["slov", 7, 1],
        ["hetslov", 9, 1]
    ];

    /** @const */ var /** Array<int> */ g_v = [17, 65, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48, 2, 142];

    /** @const */ var /** Array<int> */ g_s_ending = [119, 125, 148, 1];

    var /** number */ I_x = 0;
    var /** number */ I_p1 = 0;


    /** @return {boolean} */
    function r_mark_regions() {
        I_p1 = base.limit;
        /** @const */ var /** number */ v_1 = base.cursor;
        {
            /** @const */ var /** number */ c1 = base.cursor + 3;
            if (c1 > base.limit)
            {
                return false;
            }
            base.cursor = c1;
        }
        I_x = base.cursor;
        base.cursor = v_1;
        if (!base.go_out_grouping(g_v, 97, 248))
        {
            return false;
        }
        base.cursor++;
        if (!base.go_in_grouping(g_v, 97, 248))
        {
            return false;
        }
        base.cursor++;
        I_p1 = base.cursor;
        lab0: {
            if (I_p1 >= I_x)
            {
                break lab0;
            }
            I_p1 = I_x;
        }
        return true;
    };

    /** @return {boolean} */
    function r_main_suffix() {
        var /** number */ among_var;
        if (base.cursor < I_p1)
        {
            return false;
        }
        /** @const */ var /** number */ v_1 = base.limit_backward;
        base.limit_backward = I_p1;
        base.ket = base.cursor;
        among_var = base.find_among_b(a_1);
        if (among_var == 0)
        {
            base.limit_backward = v_1;
            return false;
        }
        base.bra = base.cursor;
        base.limit_backward = v_1;
        switch (among_var) {
            case 1:
                if (!base.slice_del())
                {
                    return false;
                }
                break;
            case 2:
                among_var = base.find_among_b(a_0);
                switch (among_var) {
                    case 1:
                        if (!base.slice_del())
                        {
                            return false;
                        }
                        break;
                }
                break;
            case 3:
                lab0: {
                    /** @const */ var /** number */ v_2 = base.limit - base.cursor;
                    lab1: {
                        if (!(base.in_grouping_b(g_s_ending, 98, 122)))
                        {
                            break lab1;
                        }
                        break lab0;
                    }
                    base.cursor = base.limit - v_2;
                    lab2: {
                        if (!(base.eq_s_b("r")))
                        {
                            break lab2;
                        }
                        {
                            /** @const */ var /** number */ v_3 = base.limit - base.cursor;
                            lab3: {
                                if (!(base.eq_s_b("e")))
                                {
                                    break lab3;
                                }
                                break lab2;
                            }
                            base.cursor = base.limit - v_3;
                        }
                        break lab0;
                    }
                    base.cursor = base.limit - v_2;
                    if (!(base.eq_s_b("k")))
                    {
                        return false;
                    }
                    if (!(base.out_grouping_b(g_v, 97, 248)))
                    {
                        return false;
                    }
                }
                if (!base.slice_del())
                {
                    return false;
                }
                break;
            case 4:
                if (!base.slice_from("er"))
                {
                    return false;
                }
                break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_consonant_pair() {
        /** @const */ var /** number */ v_1 = base.limit - base.cursor;
        if (base.cursor < I_p1)
        {
            return false;
        }
        /** @const */ var /** number */ v_2 = base.limit_backward;
        base.limit_backward = I_p1;
        base.ket = base.cursor;
        if (base.find_among_b(a_2) == 0)
        {
            base.limit_backward = v_2;
            return false;
        }
        base.bra = base.cursor;
        base.limit_backward = v_2;
        base.cursor = base.limit - v_1;
        if (base.cursor <= base.limit_backward)
        {
            return false;
        }
        base.cursor--;
        base.bra = base.cursor;
        if (!base.slice_del())
        {
            return false;
        }
        return true;
    };

    /** @return {boolean} */
    function r_other_suffix() {
        if (base.cursor < I_p1)
        {
            return false;
        }
        /** @const */ var /** number */ v_1 = base.limit_backward;
        base.limit_backward = I_p1;
        base.ket = base.cursor;
        if (base.find_among_b(a_3) == 0)
        {
            base.limit_backward = v_1;
            return false;
        }
        base.bra = base.cursor;
        base.limit_backward = v_1;
        if (!base.slice_del())
        {
            return false;
        }
        return true;
    };

    this.stem = /** @return {boolean} */ function() {
        /** @const */ var /** number */ v_1 = base.cursor;
        r_mark_regions();
        base.cursor = v_1;
        base.limit_backward = base.cursor; base.cursor = base.limit;
        /** @const */ var /** number */ v_2 = base.limit - base.cursor;
        r_main_suffix();
        base.cursor = base.limit - v_2;
        /** @const */ var /** number */ v_3 = base.limit - base.cursor;
        r_consonant_pair();
        base.cursor = base.limit - v_3;
        /** @const */ var /** number */ v_4 = base.limit - base.cursor;
        r_other_suffix();
        base.cursor = base.limit - v_4;
        base.cursor = base.limit_backward;
        return true;
    };

    /**@return{string}*/
    this['stemWord'] = function(/**string*/word) {
        base.setCurrent(word);
        this.stem();
        return base.getCurrent();
    };
};
